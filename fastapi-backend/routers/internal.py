# AI 引擎内部只读查询接口
# 仅供 python-ai 服务间调用：只读 + token 鉴权（X-Internal-Token），与用户 JWT 完全隔离。
# 安全约束：所有查询强制绑定 user_id，AI 引擎侧由系统注入，LLM 无法伪造。

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pymysql.connections import Connection

from config import settings
from database import get_db
from repositories import story_repository

router = APIRouter(prefix="/internal", tags=["internal"])


def verify_internal_token(x_internal_token: str = Header(...)) -> None:
    """校验 AI 引擎内部调用 token。

    token 未配置或不匹配时一律拒绝（403），避免未初始化时裸奔。
    """
    if not settings.INTERNAL_AI_TOKEN or x_internal_token != settings.INTERNAL_AI_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="内部接口 token 无效",
        )


def _trim(value, max_len: int) -> str:
    """把数据库字段截断到指定长度（None 转空字符串），控制返回体积。"""
    if value is None:
        return ""
    text = str(value)
    return text[:max_len]


@router.get("/stories/search")
def search_stories(
    user_id: int = Query(..., description="用户 ID（系统注入，禁止 LLM 传入他人 ID）"),
    keyword: str | None = Query(None, description="按标题/摘要模糊过滤"),
    limit: int = Query(20, ge=1, le=50),
    conn: Connection = Depends(get_db),
    _token: None = Depends(verify_internal_token),
):
    """查询当前用户的漫剧列表（最小字段，供 ReAct 真实读数据）。"""
    rows = story_repository.find_by_user_id_paginated(conn, user_id, 0, limit)

    # keyword 在 Python 侧过滤，不改 SQL（title/synopsis 包含关键词）
    if keyword:
        kw = keyword.lower()
        rows = [
            row for row in rows
            if kw in str(row.get("title") or "").lower()
            or kw in str(row.get("synopsis") or "").lower()
        ]

    # 只返回最小字段，控制 LLM token 成本
    return [
        {
            "id": row.get("id"),
            "title": row.get("title"),
            "genre": row.get("genre"),
            "style": row.get("style"),
            "status": row.get("status"),
            "synopsis": _trim(row.get("synopsis"), 200),
        }
        for row in rows
    ]


@router.get("/stories/{story_id}")
def get_story_detail(
    story_id: int,
    user_id: int = Query(..., description="用户 ID（系统注入，禁止 LLM 传入他人 ID）"),
    conn: Connection = Depends(get_db),
    _token: None = Depends(verify_internal_token),
):
    """查询指定漫剧详情（自带归属校验，越权/不存在返回 404）。"""
    row = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="漫剧不存在或无权访问",
        )

    # 只返回最小字段，full_content 截断到 2000 字符
    return {
        "id": row.get("id"),
        "title": row.get("title"),
        "genre": row.get("genre"),
        "style": row.get("style"),
        "status": row.get("status"),
        "synopsis": _trim(row.get("synopsis"), 200),
        "full_content": _trim(row.get("full_content"), 2000),
    }
