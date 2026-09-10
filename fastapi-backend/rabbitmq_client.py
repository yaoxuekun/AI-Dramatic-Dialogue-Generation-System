import pika
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exceptions import AMQPConnectionError
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

# 全局 RabbitMQ 连接实例
_connection: Optional[BlockingConnection] = None


def _get_connection_params() -> ConnectionParameters:
    """创建RabbitMQ连接参数"""
    credentials = PlainCredentials(
        username=settings.RABBITMQ_USER, password=settings.RABBITMQ_PASSWORD
    )
    return ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        virtual_host=settings.RABBITMQ_VHOST,
        credentials=credentials,
        heartbeat=60,  # 心跳间隔，防止防火墙断开长连接
        blocked_connection_timeout=300,  # 连接阻塞超时（秒）
    )


def init_rabbitmq() -> None:
    """
    初始化RabbitMQ连接，并声明交换机和队列。
    此函数在应用启动时调用。
    """
    global _connection

    if _connection is not None and _connection.is_open:
        logger.info("RabbitMQ 连接已存在，跳过初始化")
        return

    try:
        # 1.建立连接
        _connection = BlockingConnection(_get_connection_params())
        logger.info("RabbitMQ 连接建立成功")

        # 2.创建信道
        channel = _connection.channel()

        # 3.声明交换机（持久化，确保 RabbitMQ 重启后交换机不丢失）
        channel.exchange_declare(
            exchange=settings.RABBITMQ_EXCHANGE,
            exchange_type=settings.RABBITMQ_EXCHANGE_TYPE,
            durable=True,  # 持久化
            auto_delete=False,
        )
        logger.info(f"交换机{settings.RABBITMQ_EXCHANGE}声明成功")

        # 4.声明队列（持久化）
        queues = [
            (
                settings.RABBITMQ_QUEUE_STORY_REQUEST,
                settings.RABBITMQ_ROUTING_KEY_STORY_REQUEST,
            ),
            (
                settings.RABBITMQ_QUEUE_STORY_RESULT,
                settings.RABBITMQ_ROUTING_KEY_STORY_RESULT,
            ),
            (
                settings.RABBITMQ_QUEUE_CHAT_PERSIST,
                settings.RABBITMQ_ROUTING_KEY_CHAT_PERSIST,
            ),
        ]
        for queue_name, routing_key in queues:
            # 声明队列：持久化，非独占，不自动删除
            channel.queue_declare(
                queue=queue_name,
                durable=True,
                exclusive=False,
                auto_delete=False,
            )
            # 绑定队列到交换机
            channel.queue_bind(
                queue=queue_name,
                exchange=settings.RABBITMQ_EXCHANGE,
                routing_key=routing_key,
            )
            logger.info(f"队列{queue_name}已声明，并绑定路由键{routing_key}成功")

        # 5.关闭信道（连接保持打开）
        channel.close()
        logger.info("RabbitMQ 初始化和队列声明全部完成")
    except AMQPConnectionError as e:
        logger.error(f"RabbitMQ 连接失败:{e}")
        raise
    except Exception as e:
        logger.error(f"RabbitMQ 初始化异常:{e}")
        raise


def get_connection() -> BlockingConnection:
    """获取全局RabbitMQ连接（供发布者和消费者使用）"""
    if _connection is None or not _connection.is_open:
        logger.warning("RabbitMQ 连接不可用，正在重新初始化...")
        init_rabbitmq()
    return _connection


def test_rabbitmq_connection() -> bool:
    """
    测试 RabbitMQ 是否连通
    尝试打开一个信道并关闭，能成功说明连接正常。
    """
    try:
        conn = get_connection()
        channel = conn.channel()
        channel.close()
        return True
    except Exception as e:
        logger.error(f"RabbitMQ 连通性测试失败：{e}")
        return False


def publish_message(
    routing_key: str,
    message_body: str,
    properties: Optional[pika.BasicProperties] = None,
) -> None:
    """
    通用消息发布函数。

    Args:
    routing_key:路由键（决定消息进入哪个队列）
    message_body:消息内容（JSON字符串或纯文本）
    properties:消息属性（如持久化、优先级等）
    """

    conn = get_connection()
    channel = conn.channel()

    try:
        if properties is None:
            # 默认消息持久化（delivery_mode=2）,避免 RabbitMQ 重启丢消息
            properties = pika.BasicProperties(delivery_mode=2)

        channel.basic_publish(
            exchange=settings.RABBITMQ_EXCHANGE,
            routing_key=routing_key,
            body=message_body.encode("utf-8"),
            properties=properties,
        )
        logger.debug(
            f"消息发布成功:routing_key={routing_key},body={message_body[:50]}..."
        )
    except Exception as e:
        logger.error(f"消息发布失败:{e}")
        raise
    finally:
        channel.close()
