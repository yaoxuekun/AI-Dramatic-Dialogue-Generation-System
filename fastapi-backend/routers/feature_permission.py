# routers/feature_permission.py
from fastapi import APIRouter, Depends, HTTPException, status
from pymysql.connections import Connection

from database import get_db
from dependencies import get_current_user, require_root
from schemas.common import success_response
from schemas.feature_permission import FeaturePermissionUpdate
from repositories import feature_permission_repository

router = APIRouter()


@router.get("/feature-permissions")
def get_feature_permissions(
    current_user: dict = Depends(require_root),
    conn: Connection = Depends(get_db),
):
    """获取功能权限列表（需要 ROOT 权限）"""
    permissions = feature_permission_repository.find_all(conn)
    return success_response(data=permissions, message="获取成功")


@router.put("/feature-permissions/{permission_id}")
def update_feature_permission(
    permission_id: int,
    req: FeaturePermissionUpdate,
    current_user: dict = Depends(require_root),
    conn: Connection = Depends(get_db),
):
    """修改功能权限（需要 ROOT 权限），root 始终保留"""
    existing = feature_permission_repository.find_by_id(conn, permission_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="功能权限不存在",
        )

    # 确保 ROOT 始终在 allowed_roles 中
    allowed_roles = req.allowed_roles
    if allowed_roles is not None:
        roles = [r.strip() for r in allowed_roles.split(",") if r.strip()]
        if "ROOT" not in roles:
            roles.append("ROOT")
        allowed_roles = ",".join(roles)

    feature_permission_repository.update(
        conn,
        permission_id=permission_id,
        allowed_roles=allowed_roles,
        enabled=req.enabled,
    )

    return success_response(message="修改成功")


@router.get("/feature-permissions/me")
def get_my_feature_permissions(
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """获取当前用户可用的功能 key 列表"""
    role = current_user.get("role", "USER")
    keys = feature_permission_repository.find_enabled_keys_by_role(conn, role)
    return success_response(data=keys, message="获取成功")
