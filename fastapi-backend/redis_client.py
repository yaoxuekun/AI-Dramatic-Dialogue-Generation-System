# 使用redis-py链接Redis
import redis
from redis import Redis
from config import settings
import logging
from typing import Optional, Generator

logger = logging.getLogger(__name__)  # 日志记录器：有则返回已有实例，无则新建
_client: Optional[Redis] = None


def init_redis_pool() -> None:
    """
    初始化 Redis 连接池。
    由于 redis.Redis 内部默认使用连接池，我们只需创建客户端即可。
    设置 decode_responses=True 让它自动解码返回的字符串，省去手动 decode 的麻烦。
    （连接池会在进程退出时自动释放，所以无需显示关闭）
    """
    global _client
    if _client is not None:
        return

    try:
        # 创建池
        pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            protocol=2,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=settings.REDIS_DECODE_RESPONSES,
        )
        _client = redis.Redis(connection_pool=pool)
        logger.info(
            f"Redis 连接池初始化成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        )
    except Exception as e:
        logger.error(f"Redis 连接池初始化失败: {e}")
        raise


def get_redis() -> Redis:
    if _client is None:
        init_redis_pool()
    return _client


def test_redis_connection() -> bool:
    """
    测试redis是否连通。
    调用ping()方法，返回True标识正常，否则抛出异常。
    """
    try:
        client = get_redis()
        return client.ping()
    except Exception as e:
        logger.error(f"Reid连通性测试失败:{e}")
        return False
