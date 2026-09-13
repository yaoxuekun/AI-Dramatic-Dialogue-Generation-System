"""
Redis 中维护已删除漫剧 ID 的集合，供 result_consumer 跳过无效消息。
"""

import redis_client

KEY = "aisay:deleted_stories"
EXPIRE_SECONDS = 86400 * 7  # 7 天后自动清理


def mark_deleted(story_id: int) -> None:
    """标记漫剧为已删除。"""
    r = redis_client.get_redis()
    r.sadd(KEY, story_id)
    r.expire(KEY, EXPIRE_SECONDS)


def is_deleted(story_id: int) -> bool:
    """检查漫剧是否已被删除。"""
    r = redis_client.get_redis()
    return r.sismember(KEY, story_id)
