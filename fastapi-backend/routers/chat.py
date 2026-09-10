# routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
import httpx
import json
import logging
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
from pymysql.connections import Connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat")

@router.post("/start")
def start_chat(
    req: ChatStartRequest,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """创建新对话"""

    user_id = current_user["id"]
    session_id = session_repo.create_session(conn, user_id, req.title)
    if not session_id:
        raise HTTPException(status_code=500, detail="会话创建失败")

    session = session_repo.find_by_id(conn, session_id, user_id)
    if session is None:
        raise HTTPException(status_code=500, detail="会话查询失败")

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

    # 1. 校验会话归属
    session = session_repo.find_by_id(conn, session_id, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在或无权访问"
        )

    # 2. 保存用户消息
    msg_repo.insert_message(conn, session_id, "user", req.content)

    # 3. 构建 AI 请求上下文
    context_data = session.get("context_data")
    if isinstance(context_data, str):
        try:
            context_data = json.loads(context_data)
        except (json.JSONDecodeError, TypeError):
            context_data = {}

    # 获取近期消息作为短期记忆
    recent_rows = msg_repo.find_by_session(conn, session_id, 20)
    recent_messages = [
        {"role": m["role"], "content": m["content"], "createdAt": str(m.get("created_at", ""))}
        for m in recent_rows
    ]

    # 获取绑定漫剧的上下文
    story_context: Dict[str, Any] = {}
    story_id = session.get("story_id")
    if story_id:
        story = story_repository.find_by_id(conn, story_id)
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

    # 5. 保存 AI 回复
    assistant_message = ai_result.get("assistantMessage", "抱歉，我暂时无法回复。")
    ai_metadata = {
        "route": ai_result.get("route"),
        "module": ai_result.get("module"),
        "intent": ai_result.get("intent"),
        "javaMethod": ai_result.get("javaMethod"),
        "javaMethodArgs": ai_result.get("javaMethodArgs"),
        "missingInfo": ai_result.get("missingInfo"),
    }
    msg_repo.insert_message(conn, session_id, "ai", assistant_message, metadata=ai_metadata)

    # 6. 更新会话记忆（longTermMemory + keyFacts 存入 context_data）
    new_context = context_data or {}
    if ai_result.get("longTermMemory") is not None:
        new_context["longTermMemory"] = ai_result["longTermMemory"]
    if ai_result.get("keyFacts"):
        new_context["keyFacts"] = ai_result["keyFacts"]
    cur = conn.cursor()
    cur.execute(
        "UPDATE chat_sessions SET context_data = %s, last_active = NOW() WHERE id = %s",
        (json.dumps(new_context, ensure_ascii=False), session_id),
    )
    conn.commit()

    # 7. 返回最新 AI 消息
    messages = msg_repo.find_by_session(conn, session_id, 10)
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="消息保存失败"
        )
    ai_msg = messages[-1]
    return success_response(
        data=MessageResponse(**ai_msg).model_dump(by_alias=True), message="消息发送成功"
    )


@router.get("/history/{sessionId}")
def get_history(
    sessionId: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """获取会话历史信息"""
    user_id = current_user["id"]
    session = session_repo.find_by_id(conn, sessionId, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在或无权访问"
        )
    messages = msg_repo.find_by_session(conn, sessionId)
    return success_response(
        data=[MessageResponse(**m).model_dump(by_alias=True) for m in messages]
    )


@router.get("/sessions")
def list_sessions(
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """获取当前用户的所有会话列表"""
    user_id = current_user["id"]
    sessions = session_repo.find_by_user(conn, user_id)
    return success_response(
        data=[ChatSessionResponse(**s).model_dump(by_alias=True) for s in sessions]
    )


@router.delete("/session/{sessionId}")
def delete_session(
    sessionId: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """软删除会话"""
    user_id = current_user["id"]
    deleted = session_repo.soft_delete(conn, sessionId, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在或已删除"
        )

    return success_response(data=None, message="会话已删除")
