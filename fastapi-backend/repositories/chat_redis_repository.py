# repositories/chat_redis_repository.py
"""
Redis 聊天存储层
核心思想：
  读时优先看 Redis，没有再看 MySQL，找到后回填 Redis；
  写时优先写 Redis，然后发 RabbitMQ，让消费者写入 MySQL。

Redis 数据结构：
  chat:session:{session_id}           → Hash  (会话字段)
  chat:user:{user_id}:sessions        → Sorted Set  (score=last_active 毫秒时间戳, member=session_id)
  chat:session:{session_id}:messages  → List  (JSON 编码的消息)
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import redis

import database
from redis_client import get_redis
from repositories import chat_session_repository
from services.task_publisher import publish_chat_persist

logger = logging.getLogger(__name__)

# 消息列表最大长度，防止无限增长
MAX_MESSAGES = 500

# Redis key 模板
_KEY_SESSION = "chat:session:{}"
_KEY_USER_SESSIONS = "chat:user:{}:sessions"
_KEY_MESSAGES = "chat:session:{}:messages"


# ── 1. save_session ────────────────────────────────────────────────

def save_session(session_id: int, session_data: Dict[str, Any]) -> None:
    """保存会话到 Redis Hash，并将 session_id 加入用户的 Sorted Set。

    Args:
        session_id: 会话 ID。
        session_data: 会话字段字典，需包含 user_id 和 last_active。
    """
    r = get_redis()
    key = _KEY_SESSION.format(session_id)

    # 将所有字段转为字符串存入 Hash
    flat: Dict[str, str] = {}
    for k, v in session_data.items():
        if v is None:
            flat[k] = ""
        elif isinstance(v, (dict, list)):
            flat[k] = json.dumps(v, ensure_ascii=False)
        else:
            flat[k] = str(v)

    r.hset(key, mapping=flat)

    # 加入用户会话列表
    user_id = session_data.get("user_id")
    last_active = session_data.get("last_active")
    if user_id is not None:
        add_session_to_user_list(int(user_id), session_id, last_active)

    logger.debug(f"[chat-redis] session saved: {session_id}")


# ── 2. get_session ─────────────────────────────────────────────────

def get_session(session_id: int) -> Optional[Dict[str, Any]]:
    """从 Redis 读取会话，未命中则回查 MySQL 并回填。

    Returns:
        会话字典，不存在返回 None。
    """
    r = get_redis()
    key = _KEY_SESSION.format(session_id)

    # 尝试 Redis
    data = r.hgetall(key)
    if data:
        return _decode_session(data)

    # 回查 MySQL
    with database.get_db_cursor(commit=False) as conn:
        row = chat_session_repository.find_by_id(conn, session_id)

    if row:
        # 回填 Redis
        save_session(session_id, row)
        return row

    return None


# ── 3. add_session_to_user_list ────────────────────────────────────

def add_session_to_user_list(
    user_id: int, session_id: int, last_active: Any = None
) -> None:
    """将 session_id 加入用户的 Sorted Set（score = last_active 毫秒时间戳）。

    Args:
        user_id: 用户 ID。
        session_id: 会话 ID。
        last_active: 最后活跃时间，可以是 datetime / timestamp / str / None。
    """
    r = get_redis()
    key = _KEY_USER_SESSIONS.format(user_id)
    score = _to_timestamp_ms(last_active) if last_active is not None else int(time.time() * 1000)
    r.zadd(key, {str(session_id): score})


# ── 4. get_user_sessions ───────────────────────────────────────────

def get_user_sessions(user_id: int) -> List[Dict[str, Any]]:
    """读取用户的会话列表（按 last_active 倒序）。

    先从 Redis Sorted Set 获取 session_id 列表，
    逐个从 Redis Hash 读取，未命中则回查 MySQL。
    """
    r = get_redis()
    set_key = _KEY_USER_SESSIONS.format(user_id)

    # 倒序获取所有 session_id
    session_id_strs: List[str] = r.zrevrange(set_key, 0, -1)
    if not session_id_strs:
        # Redis 无数据，回查 MySQL
        with database.get_db_cursor(commit=False) as conn:
            rows = chat_session_repository.find_by_user(conn, user_id)
        # 回填
        for row in rows:
            sid = row["id"]
            save_session(sid, row)
        return rows

    sessions: List[Dict[str, Any]] = []
    for sid_str in session_id_strs:
        sid = int(sid_str)
        session = get_session(sid)
        if session:
            sessions.append(session)

    return sessions


# ── 5. delete_session ──────────────────────────────────────────────

def delete_session(user_id: int, session_id: int) -> None:
    """从用户会话列表移出会话，并删除会话 Hash 和消息列表。"""
    r = get_redis()
    user_key = _KEY_USER_SESSIONS.format(user_id)
    session_key = _KEY_SESSION.format(session_id)
    messages_key = _KEY_MESSAGES.format(session_id)

    pipe = r.pipeline()
    pipe.zrem(user_key, str(session_id))
    pipe.delete(session_key)
    pipe.delete(messages_key)
    pipe.execute()

    logger.debug(f"[chat-redis] session deleted: {session_id}")


# ── 6. append_message ──────────────────────────────────────────────

def append_message(session_id: int, message_data: Dict[str, Any]) -> None:
    """追加消息到 Redis List，并通过 RabbitMQ 异步写入 MySQL。

    Args:
        session_id: 会话 ID。
        message_data: 消息字典，需包含 role、content 等字段。
    """
    r = get_redis()
    key = _KEY_MESSAGES.format(session_id)

    encoded = json.dumps(message_data, ensure_ascii=False, default=str)
    r.rpush(key, encoded)

    # 裁剪到最大长度
    r.ltrim(key, -MAX_MESSAGES, -1)

    # 异步持久化到 MySQL
    try:
        publish_chat_persist("MESSAGE_INSERT", {
            "sessionId": session_id,
            "message": message_data,
        })
    except Exception as exc:
        logger.error(f"[chat-redis] 发布消息持久化失败: {exc}")

    logger.debug(f"[chat-redis] message appended: session={session_id}")


# ── 7. get_messages ────────────────────────────────────────────────

def get_messages(session_id: int) -> List[Dict[str, Any]]:
    """读取消息列表。

    先从 Redis List 读取，未命中则回查 MySQL 并回填。
    """
    r = get_redis()
    key = _KEY_MESSAGES.format(session_id)

    items = r.lrange(key, 0, -1)
    if items:
        return [json.loads(item) for item in items]

    # 回查 MySQL（messages 表）
    with database.get_db_cursor(commit=False) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, session_id, role, content, metadata, created_at "
            "FROM messages WHERE session_id = %s ORDER BY id ASC",
            (session_id,),
        )
        rows = cur.fetchall()

    if rows:
        # 回填 Redis
        encoded = [json.dumps(row, ensure_ascii=False, default=str) for row in rows]
        if encoded:
            r.rpush(key, *encoded)
        return rows

    return []


# ── 内部工具 ───────────────────────────────────────────────────────

def _decode_session(data: Dict[str, str]) -> Dict[str, Any]:
    """将 Redis Hash 中的字符串值还原为 Python 类型。"""
    result: Dict[str, Any] = {}
    for k, v in data.items():
        if v == "":
            result[k] = None
        elif k in ("context_data",):
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                result[k] = v
        elif k in ("id", "user_id", "story_id", "progress_percentage"):
            try:
                result[k] = int(v)
            except (ValueError, TypeError):
                result[k] = v
        else:
            result[k] = v
    return result


def _to_timestamp_ms(value: Any) -> int:
    """将 datetime / timestamp / 字符串转为毫秒时间戳。"""
    if isinstance(value, (int, float)):
        return int(value * 1000) if value < 1e12 else int(value)
    if hasattr(value, "timestamp"):
        return int(value.timestamp() * 1000)
    try:
        from datetime import datetime
        if isinstance(value, str):
            # 尝试常见格式
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return int(datetime.strptime(value, fmt).timestamp() * 1000)
                except ValueError:
                    continue
    except Exception:
        pass
    return int(time.time() * 1000)
