"""
- 实现 generate_token(user_id, username) → 返回 JWT 字符串
- 实现 validate_token(token) → 返回 bool
- 实现 get_user_id_from_token(token) → 返回 user_id
- 实现 get_username_from_token(token) → 返回 username
- JWT payload 包含：userId、username、iat（签发时间）、exp（过期时间）
- 默认有效期 24 小时
参考：backend/src/main/java/com/aisay/manga/utils/JwtUtil.java
"""

from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Optional
from config import settings


def generate_token(user_id: int, username: str) -> str:
    """生成JWT，有效期24小时"""
    payload = {
        "userId": user_id,
        "username": username,
        "iat": datetime.now(timezone.utc),  # 签发时间
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=settings.JWT_EXPIRATION_HOURS),  # 过期时间
    }

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def validate_token(token: str) -> bool:
    """验证token是否有效"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return True
    except JWTError:
        return False


def get_user_id_from_token(token: str) -> Optional[int]:
    """从 token 中提取 userId，失败返回 None"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("userId")
    except JWTError:
        return None


def get_username_from_token(token: str) -> Optional[str]:
    """从 token 中提取用户名，失败返回None"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("username")
    except JWTError:
        return None


def decode_token(token: str) -> Optional[dict]:
    """
    解码 token 返回完整 payload（用于调试或额外信息）。
    :param token: JWT 字符串
    :return: payload 字典或 None
    """
    try:
        return jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        return None
