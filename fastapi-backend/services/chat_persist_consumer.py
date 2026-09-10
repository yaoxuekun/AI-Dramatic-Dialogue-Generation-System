"""
聊天持久化消费者

消费队列：aisay.chat.persist

事件类型：SESSION_UPSERT、MESSAGE_INSERT

消息格式：
{
    "eventType": "...",
    "data": { ... }
}

结构类似 result_consumer.py：daemon 线程 + 5 秒重连 + basic_ack
函数 start_chat_persist_consumer()：main 的 lifespan 中调用
"""

import json
import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

import pika

from config import settings
import database

logger = logging.getLogger(__name__)

_consumer_thread: Optional[threading.Thread] = None


# ── 公共入口 ────────────────────────────────────────────────────────

def start_chat_persist_consumer() -> None:
    """启动聊天持久化消费线程（FastAPI lifespan 中调用）。"""
    global _consumer_thread
    if _consumer_thread and _consumer_thread.is_alive():
        return
    _consumer_thread = threading.Thread(
        target=_reconnect_loop, name="aisay-chat-persist-consumer", daemon=True
    )
    _consumer_thread.start()
    logger.info("[chat-persist] 后台消费线程已启动")


# ── 内部：连接循环 ──────────────────────────────────────────────────

def _reconnect_loop() -> None:
    """异常断开后自动重连的外层循环。"""
    while True:
        try:
            _consume_forever()
        except Exception as exc:
            logger.error(f"[chat-persist] 连接异常: {exc}，5 秒后重试")
            time.sleep(5)


def _consume_forever() -> None:
    """声明队列拓扑并持续消费聊天持久化消息。"""
    credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        virtual_host=settings.RABBITMQ_VHOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # 声明交换机和队列（与 rabbitmq_client.init_rabbitmq 保持一致）
    channel.exchange_declare(
        exchange=settings.RABBITMQ_EXCHANGE, exchange_type="direct", durable=True
    )
    channel.queue_declare(queue=settings.RABBITMQ_QUEUE_CHAT_PERSIST, durable=True)
    channel.queue_bind(
        queue=settings.RABBITMQ_QUEUE_CHAT_PERSIST,
        exchange=settings.RABBITMQ_EXCHANGE,
        routing_key=settings.RABBITMQ_ROUTING_KEY_CHAT_PERSIST,
    )
    channel.basic_qos(prefetch_count=1)

    def on_message(ch: Any, method: Any, properties: Any, body: bytes) -> None:
        message = json.loads(body.decode("utf-8"))
        event_type = message.get("eventType", "UNKNOWN")
        data = message.get("data", {})
        logger.info(f"[chat-persist] 收到事件: eventType={event_type}")
        try:
            _dispatch(event_type, data)
        except Exception as exc:
            logger.error(f"[chat-persist] 处理失败: {exc}", exc_info=True)
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=settings.RABBITMQ_QUEUE_CHAT_PERSIST, on_message_callback=on_message
    )
    logger.info(
        f"[chat-persist] 开始消费队列 {settings.RABBITMQ_QUEUE_CHAT_PERSIST}"
    )
    channel.start_consuming()


# ── 内部：事件分发 ──────────────────────────────────────────────────

def _dispatch(event_type: str, data: Dict[str, Any]) -> None:
    """按 eventType 分发到对应落库逻辑。"""
    if event_type == "SESSION_UPSERT":
        _upsert_session(data)
    elif event_type == "MESSAGE_INSERT":
        _insert_message(data)
    else:
        logger.warning(f"[chat-persist] 未知事件类型: {event_type}")


# ── 内部：落库函数 ──────────────────────────────────────────────────

def _upsert_session(data: Dict[str, Any]) -> None:
    """插入或更新 chat_sessions 记录。"""
    session_id = data.get("id")
    if not session_id:
        logger.warning("[chat-persist] SESSION_UPSERT 缺少 id，跳过")
        return

    with database.get_db_cursor() as conn:
        cur = conn.cursor()
        now = datetime.now()
        cur.execute(
            """INSERT INTO chat_sessions
               (id, user_id, story_id, session_key, title, context_data,
                current_stage, progress_percentage, status, started_at, last_active)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
               title = VALUES(title),
               context_data = VALUES(context_data),
               current_stage = VALUES(current_stage),
               progress_percentage = VALUES(progress_percentage),
               status = VALUES(status),
               last_active = VALUES(last_active)""",
            (
                session_id,
                data.get("user_id"),
                data.get("story_id"),
                data.get("session_key", ""),
                data.get("title", ""),
                json.dumps(data.get("context_data"), ensure_ascii=False) if data.get("context_data") else None,
                data.get("current_stage", "INITIAL"),
                data.get("progress_percentage", 0),
                data.get("status", "active"),
                data.get("started_at", now),
                data.get("last_active", now),
            ),
        )
    logger.info(f"[chat-persist] 会话已持久化: sessionId={session_id}")


def _insert_message(data: Dict[str, Any]) -> None:
    """插入 messages 记录。"""
    session_id = data.get("sessionId")
    message = data.get("message", {})
    if not session_id or not message:
        logger.warning("[chat-persist] MESSAGE_INSERT 缺少 sessionId 或 message，跳过")
        return

    with database.get_db_cursor() as conn:
        cur = conn.cursor()
        metadata = message.get("metadata")
        cur.execute(
            """INSERT INTO messages (session_id, role, content, metadata, created_at)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                session_id,
                message.get("role", ""),
                message.get("content", ""),
                json.dumps(metadata, ensure_ascii=False) if metadata else None,
                message.get("created_at", datetime.now()),
            ),
        )
    logger.debug(f"[chat-persist] 消息已持久化: sessionId={session_id}")
