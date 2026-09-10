"""
任务发布服务
负责将 AI 任务和聊天持久化事件投递到 RabbitMQ。
"""

import json
import logging
import pika
from typing import Any, Dict, Optional

from config import settings
import rabbitmq_client

logger = logging.getLogger(__name__)


def publish_story_task(task_message: Dict[str, Any]) -> None:
    """发布 AI 故事任务到交换机 aisay.ai.exchange，路由键 ai.story.request。

    Args:
        task_message: 任务消息体，需包含 taskType、storyId、userId 等字段。
    """
    body = json.dumps(task_message, ensure_ascii=False)
    properties = pika.BasicProperties(
        delivery_mode=2,
        content_type="application/json",
    )
    rabbitmq_client.publish_message(
        routing_key=settings.RABBITMQ_ROUTING_KEY_STORY_REQUEST,
        message_body=body,
        properties=properties,
    )
    logger.info(
        f"已发布故事任务: taskType={task_message.get('taskType')}, "
        f"storyId={task_message.get('storyId')}"
    )


def publish_chat_persist(event_type: str, data: Dict[str, Any]) -> None:
    """发布聊天持久化事件到队列 aisay.chat.persist。

    Args:
        event_type: 事件类型，如 SESSION_UPSERT、MESSAGE_INSERT。
        data: 事件数据。
    """
    body = json.dumps({"eventType": event_type, "data": data}, ensure_ascii=False)
    properties = pika.BasicProperties(
        delivery_mode=2,
        content_type="application/json",
    )
    rabbitmq_client.publish_message(
        routing_key=settings.RABBITMQ_ROUTING_KEY_CHAT_PERSIST,
        message_body=body,
        properties=properties,
    )
    logger.info(f"已发布聊天持久化事件: eventType={event_type}")
