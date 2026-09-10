"""
- POST /api/auth/register：
  - 请求体：{username, email, password}
  - 校验：username 唯一、email 唯一、格式校验
  - 逻辑：BCrypt 加密密码，插入 users 表
  - 响应：返回 UserProfileResponse（不返回 token）
- POST /api/auth/login：
  - 请求体：{username, password}
  - 逻辑：按 username 查询用户，BCrypt 校验密码，生成 JWT
  - 响应：返回 {token, userId, username}
- GET /api/user/profile（需认证）：
  - 逻辑：按当前用户 ID 查询
  - 响应：返回 {id, username, email, avatarPath, createdAt, role}
- PUT /api/user/profile（需认证）：
  - 请求体：{username?, email?, avatarPath?}
  - 逻辑：只更新非 null 字段，做唯一性校验
  - 响应：返回更新后的 UserProfileResponse
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pymysql.connections import Connection
from datetime import datetime
from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    UserProfileResponse,
)
from schemas.common import success_response
from database import get_db
from utils.password_util import hash_password, verify_password
from utils.jwt_util import generate_token
from repositories import user_repository
import logging

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/auth",
)


@router.post("/register")
def register(req: RegisterRequest, conn: Connection = Depends(get_db)):
    """
    用户注册。
    - 校验用户名、邮箱唯一性
    - 密码 BCrypt 加密后存入数据库
    - 默认角色为 USER
    """

    # 1. 检查用户名是否已存在
    if user_repository.find_by_username(conn, req.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已被占用"
        )

    # 2.检查邮件是否已存在
    if user_repository.find_by_email(conn, req.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册"
        )

    # 3.创建用户
    hashed = hash_password(req.password)
    user_id = user_repository.create_user(conn, req.username, req.email, hashed)

    return success_response(
        data=UserProfileResponse(
            id=user_id,
            username=req.username,
            email=req.email,
            avatar_path=None,
            role="USER",
            created_at=datetime.now(),
        ).model_dump(),
        message="注册成功，请登录",
    )


@router.post("/login")
def login(req: LoginRequest, conn: Connection = Depends(get_db)):
    """
    用户登录。
    - 按用户名查询用户，BCrypt校验密码，生成JWT
    """
    # 1.查询用户
    user = user_repository.find_by_username(conn, req.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    # 2. 验证密码
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    # 3. 生成token
    token = generate_token(user["id"], user["username"])

    return success_response(
        data=LoginResponse(
            token=token,
            userId=user["id"],
            username=user["username"],
            email=user["email"],
            avatar_path=user["avatar_path"],
            role=user["role"],
        ).model_dump(),
        message="登录成功",
    )
