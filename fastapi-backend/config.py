import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # 服务地址
    HOST: str = "0.0.0.0"
    PORT: int = 8085
    DEBUG: bool = True

    # CORS 允许的来源
    ALLOW_ORIGINS: list = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    # 数据库
    MYSQL_HOST = os.getenv("mysql_host")
    MYSQL_PORT = int(os.getenv("mysql_port", 3306))
    MYSQL_USER = os.getenv("mysql_user")
    MYSQL_PASSWORD = os.getenv("mysql_password")
    MYSQL_DATABASE = os.getenv("mysql_database")
    MYSQL_CHARSET: str = "utf8mb4"

    # 连接池
    POOL_MIN_SIZE: int = 2  # 最小连接数
    POOL_MAX_SIZE: int = 10  # 最大连接数
    POOL_MAX_IDLE: int = 60  # 连接最大空闲时间（秒）
    POOL_CONN_TIMEOUT: int = 10  # 获取连接超时（秒）

    # Redis
    REDIS_HOST = os.getenv("redis_host")
    REDIS_PORT = int(os.getenv("redis_port", 6379))
    REDIS_DB = int(os.getenv("redis_db", 0))
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_DECODE_RESPONSES: bool = True

    # RabbitMQ
    RABBITMQ_HOST = os.getenv("rabbitmq_host", "localhost")
    RABBITMQ_PORT = int(os.getenv("rabbitmq_port", 5672))
    RABBITMQ_VHOST: str = os.getenv("rabbitmq_vhost", "/")  # 虚拟主机，默认
    RABBITMQ_USER = os.getenv("rabbitmq_user")
    RABBITMQ_PASSWORD = os.getenv("rabbitmq_password")
    # 交换机与队列名称
    RABBITMQ_EXCHANGE: str = "aisay.ai.exchange"
    RABBITMQ_EXCHANGE_TYPE: str = "direct"  # 直连交换机
    # 队列名及对应的路由键
    RABBITMQ_QUEUE_STORY_REQUEST: str = "aisay.ai.story.request"
    RABBITMQ_ROUTING_KEY_STORY_REQUEST: str = "ai.story.request"
    RABBITMQ_QUEUE_STORY_RESULT: str = "aisay.ai.story.result"
    RABBITMQ_ROUTING_KEY_STORY_RESULT: str = "ai.story.result"
    RABBITMQ_QUEUE_CHAT_PERSIST: str = "aisay.chat.persist"
    RABBITMQ_ROUTING_KEY_CHAT_PERSIST: str = "chat.persist"

    # JWT
    JWT_SECRET: str = os.getenv("jwt_secret")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = int(os.getenv("jwt_expiration_hours", 24))

    # Python AI 引擎
    AI_ENGINE_BASE_URL = os.getenv("ai_engine_base_url")

    # 文件存储
    STORAGE_ROOT_PATH = os.getenv("storage_root_path", "./storage")


settings = Settings()
