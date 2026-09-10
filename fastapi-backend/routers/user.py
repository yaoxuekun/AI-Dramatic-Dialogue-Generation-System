from fastapi import APIRouter, Depends, HTTPException, status
from pymysql.connections import Connection
from schemas.auth import UserProfileResponse, UserUpdateRequest, UserManageResponse, UserUpdateRoleRequest
from schemas.common import success_response
from database import get_db
from repositories import user_repository
from dependencies import get_current_user, require_root

router = APIRouter(prefix="/user")


@router.get("/profile")
def get_profile(
    current_user: dict = Depends(get_current_user), conn: Connection = Depends(get_db)
):
    user = user_repository.find_by_id(conn, current_user["id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return success_response(data=UserProfileResponse(**user).model_dump())


@router.put("/profile")
def update_profile(
    req: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    # 1.校验用户名是否被其他用户占用
    if user_repository.check_username_exists_excluding_user(
        conn, req.username, current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已被占用"
        )

    # 2. 校验邮箱是否被其他用户占用
    if req.email is not None:
        if user_repository.check_email_exists_excluding_user(
            conn, req.email, current_user["id"]
        ):
            raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 3. 更新资料
    user_repository.update_user_profile(
        conn,
        current_user["id"],
        username=req.username,
        email=req.email,
        avatar_path=req.avatar_path,
    )

    return get_profile(current_user, conn)


@router.get("/users")
def get_all_users(
    current_user: dict = Depends(require_root),
    conn: Connection = Depends(get_db),
):
    """获取所有用户列表（需要 ROOT 权限）"""
    users = user_repository.find_all_users(conn)
    return success_response(data=users, message="获取成功")


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    req: UserUpdateRoleRequest,
    current_user: dict = Depends(require_root),
    conn: Connection = Depends(get_db),
):
    """修改用户角色（需要 ROOT 权限），不能修改自己的角色"""
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色",
        )

    user = user_repository.find_by_id(conn, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    user_repository.update_user_role(conn, user_id, req.role)

    updated = user_repository.find_by_id(conn, user_id)
    return success_response(data=updated, message="修改成功")
