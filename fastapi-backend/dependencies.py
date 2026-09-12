"""
- 实现 get_current_user(request) 依赖注入函数：
  - 从 Authorization: Bearer <token> 头提取 JWT
  - 验证 token 有效性
  - 解析 user_id
  - 查询数据库获取用户信息
  - 无效 token 返回 401
- 实现 require_root(current_user) 依赖：校验 role == ROOT
- 实现 require_admin_or_root(current_user) 依赖：校验 role 为 ADMIN 或 ROOT
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from pymysql.connections import Connection
from database import get_db
from utils import jwt_util

logger = logging.getLogger(__name__)

# 配置 OAuth2 密码流（用于 Swagger 文档的认证按钮）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme), conn: Connection = Depends(get_db)
):
    """
    获取当前登录用户（核心认证依赖）
    - 提取并验证 JWT
    - 检查用户是否存在且未被删除
    - 返回用户信息字典
    """
    # 1.验证token
    if not jwt_util.validate_token(token):
        logger.warning(f"无效的token:{token[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2.提取 user_id
    user_id = jwt_util.get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少用户 ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3.查询数据库
    cursor = conn.cursor()
    cursor.execute(
        "select id,username,email,avatar_path,role,created_at from users where id = %s AND role != 'DELETED'",
        (user_id,),
    )
    user = cursor.fetchone()

    if not user:
        logger.warning(f"用户不存在或已被删除，user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被删除",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "avatar_path": user["avatar_path"],
        "role": user["role"],
        "created_at": user["created_at"],
    }


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme), conn: Connection = Depends(get_db)
):
    """可选认证（不强制登录），用于公开但需用户上下文的接口"""
    if token is None:
        return None
    try:
        return get_current_user(token, conn)
    except HTTPException:
        return None


def require_admin_or_root(current_user: dict = Depends(get_current_user)):
    """校验 ADMIN 或 ROOT"""
    if current_user["role"] not in ["ADMIN", "ROOT"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )
    return current_user


def require_root(
    current_user: dict = Depends(get_current_user), required_role: str = "USER"
):
    """校验 ROOT（严格对应清单要求）"""
    if current_user["role"] != "ROOT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限"
        )
    return current_user
