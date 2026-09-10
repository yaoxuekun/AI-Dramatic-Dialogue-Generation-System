# routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
import httpx
import json
import logging
from datetime import datetime
from typing import Any, Dict
from database import get_db
from dependencies import get_current_user
from config import settings
from schemas.chat import (
    ChatStartRequest,
    SendMessageRequest,
    ChatSessionResponse,
    MessageResponse,
)
from schemas.common import success_response
import repositories.chat_session_repository as session_repo
import repositories.message_repository as msg_repo
from repositories import story_repository
import database
from repositories import chat_redis_repository as redis_repo
from services.task_publisher import publish_chat_persist
from services.chat_dispatcher import dispatch_java_method
from pymysql.connections import Connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat")


@router.post("/start")
def start_chat(
    req: ChatStartRequest,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """创建新对话（写 Redis + 异步写 MySQL）"""
    user_id = current_user["id"]

    # 1. 写入 MySQL
    session_id = session_repo.create_session(conn, user_id, req.title, req.story_id)
    if not session_id:
        raise HTTPException(status_code=500, detail="会话创建失败")

    session = session_repo.find_by_id(conn, session_id, user_id)
    if session is None:
        raise HTTPException(status_code=500, detail="会话查询失败")

    # 2. 写入 Redis
    redis_repo.save_session(session_id, session)

    # 3. 发布持久化消息
    try:
        publish_chat_persist("SESSION_UPSERT", session)
    except Exception as e:
        logger.error(f"发布会话持久化消息失败: {e}")

    return success_response(
        data=ChatSessionResponse(**session).model_dump(by_alias=True),
        message="会话创建成功",
    )


@router.post("/message")
def send_message(
    req: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """发送消息，调用 python-ai 获取智能回复"""
    user_id = current_user["id"]
    session_id = req.session_id

    # 1. 校验会话归属（优先 Redis，回退 MySQL）
    session = redis_repo.get_session(session_id)
    if not session:
        session = session_repo.find_by_id(conn, session_id, user_id)
    if not session or session.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在或无权访问"
        )

    # 2. 保存用户消息到 Redis
    user_msg = {
        "role": "user",
        "content": req.content,
        "created_at": datetime.now().isoformat(),
    }
    redis_repo.append_message(session_id, user_msg)

    # 3. 构建 AI 请求上下文
    context_data = session.get("context_data")
    if isinstance(context_data, str):
        try:
            context_data = json.loads(context_data)
        except (json.JSONDecodeError, TypeError):
            context_data = {}

    # 获取近期消息作为短期记忆（从 Redis 读取）
    recent_messages_raw = redis_repo.get_messages(session_id)
    recent_messages = [
        {"role": m["role"], "content": m["content"], "createdAt": m.get("created_at", "")}
        for m in recent_messages_raw[-20:]
    ]

    # 获取绑定漫剧的上下文
    story_context: Dict[str, Any] = {}
    story_id = session.get("story_id")
    if story_id:
        with database.get_db_cursor(commit=False) as db_conn:
            story = story_repository.find_by_id(db_conn, story_id)
        if story:
            story_context = {
                "storyId": story_id,
                "title": story.get("title"),
                "genre": story.get("genre"),
                "storyStyle": story.get("style"),
                "synopsis": story.get("synopsis"),
                "outline": story.get("full_content"),
            }

    # 组装请求体
    ai_request = {
        "userId": user_id,
        "sessionId": session_id,
        "userMessage": req.content,
        "userRole": current_user.get("role", "USER"),
        "recentMessages": recent_messages,
        "longTermMemory": (context_data or {}).get("longTermMemory", ""),
        "keyFacts": (context_data or {}).get("keyFacts", {}),
        **story_context,
    }

    # 4. 调用 python-ai 服务
    ai_base = settings.AI_ENGINE_BASE_URL
    if not ai_base:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI 服务地址未配置",
        )

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{ai_base}/api/chat/agent", json=ai_request)
            resp.raise_for_status()
            ai_result = resp.json()
    except httpx.TimeoutException:
        logger.error(f"AI 服务超时: session={session_id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI 服务响应超时，请稍后重试",
        )
    except httpx.HTTPStatusError as exc:
        logger.error(f"AI 服务返回错误: {exc.response.status_code}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI 服务暂时不可用，请稍后重试",
        )
    except Exception as exc:
        logger.error(f"AI 服务调用失败: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI 服务暂时不可用，请稍后重试",
        )

    # 5. 执行白名单分发
    java_method = ai_result.get("javaMethod", "story.none")
    java_method_args = ai_result.get("javaMethodArgs", {})
    dispatch_result = dispatch_java_method(user_id, java_method, java_method_args)

    # 6. 保存 AI 回复到 Redis
    assistant_message = ai_result.get("assistantMessage", "抱歉，我暂时无法回复。")
    if dispatch_result:
        assistant_message = f"{assistant_message}\n\n{dispatch_result}"
    ai_metadata = {
        "route": ai_result.get("route"),
        "module": ai_result.get("module"),
        "intent": ai_result.get("intent"),
        "javaMethod": java_method,
        "javaMethodArgs": java_method_args,
        "missingInfo": ai_result.get("missingInfo"),
        "dispatchResult": dispatch_result,
    }
    ai_msg = {
        "role": "ai",
        "content": assistant_message,
        "metadata": ai_metadata,
        "created_at": datetime.now().isoformat(),
    }
    redis_repo.append_message(session_id, ai_msg)

    # 6. 更新会话记忆到 Redis
    new_context = context_data or {}
    if ai_result.get("longTermMemory") is not None:
        new_context["longTermMemory"] = ai_result["longTermMemory"]
    if ai_result.get("keyFacts"):
        new_context["keyFacts"] = ai_result["keyFacts"]
    session["context_data"] = new_context
    session["last_active"] = datetime.now().isoformat()
    redis_repo.save_session(session_id, session)

    # 7. 发布持久化消息
    try:
        publish_chat_persist("MESSAGE_INSERT", {
            "sessionId": session_id,
            "message": user_msg,
        })
        publish_chat_persist("MESSAGE_INSERT", {
            "sessionId": session_id,
            "message": ai_msg,
        })
        publish_chat_persist("SESSION_UPSERT", session)
    except Exception as e:
        logger.error(f"发布消息持久化失败: {e}")

    # 8. 返回最新 AI 消息
    return success_response(
        data=MessageResponse(
            id=0,
            session_id=session_id,
            role="ai",
            content=assistant_message,
            created_at=datetime.now(),
        ).model_dump(by_alias=True),
        message="消息发送成功",
    )


@router.get("/history/{sessionId}")
def get_history(
    sessionId: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """获取会话历史信息（优先 Redis，回退 MySQL）"""
    user_id = current_user["id"]

    # 校验会话归属
    session = redis_repo.get_session(sessionId)
    if not session:
        session = session_repo.find_by_id(conn, sessionId, user_id)
    if not session or session.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在或无权访问"
        )

    # 从 Redis 读取消息
    messages = redis_repo.get_messages(sessionId)
    return success_response(
        data=[
            MessageResponse(
                id=i,
                session_id=sessionId,
                role=m.get("role", ""),
                content=m.get("content", ""),
                created_at=m.get("created_at", ""),
            ).model_dump(by_alias=True)
            for i, m in enumerate(messages)
        ]
    )


@router.get("/sessions")
def list_sessions(
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """获取当前用户的所有会话列表（优先 Redis，回退 MySQL）"""
    user_id = current_user["id"]

    # 从 Redis 读取
    sessions = redis_repo.get_user_sessions(user_id)

    # 如果 Redis 为空，从 MySQL 读取并回填
    if not sessions:
        sessions = session_repo.find_by_user(conn, user_id)
        for s in sessions:
            redis_repo.save_session(s["id"], s)

    return success_response(
        data=[ChatSessionResponse(**s).model_dump(by_alias=True) for s in sessions]
    )


@router.delete("/session/{sessionId}")
def delete_session(
    sessionId: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """软删除会话（删除 Redis + 标记 MySQL）"""
    user_id = current_user["id"]

    # 从 Redis 删除
    redis_repo.delete_session(user_id, sessionId)

    # 标记 MySQL 删除
    deleted = session_repo.soft_delete(conn, sessionId, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在或已删除"
        )

    return success_response(data=None, message="会话已删除")
