from fastapi import APIRouter, Depends, HTTPException, status, Query
from pymysql.connections import Connection
from typing import Optional

from database import get_db
from dependencies import get_current_user, require_admin_or_root
from schemas.common import success_response
from schemas.outline_option import (
    OutlineOptionCreate,
    OutlineOptionUpdate,
    OutlineOptionResponse,
)
from repositories import outline_option_repository

router = APIRouter()


@router.get("/story-outline-options")
def get_outline_options(
    enabled: Optional[bool] = Query(None, description="按启用状态筛选"),
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """获取大纲配置列表（所有登录用户可用）"""
    options = outline_option_repository.find_all(conn, enabled=enabled)
    return success_response(data=options, message="获取成功")


@router.post("/story-outline-options")
def create_outline_option(
    req: OutlineOptionCreate,
    current_user: dict = Depends(require_admin_or_root),
    conn: Connection = Depends(get_db),
):
    """新增大纲配置（需要 ADMIN 或 ROOT 权限）"""
    # 唯一性校验：同类型下名称不能重复
    existing = outline_option_repository.find_by_type_and_name(conn, req.option_type, req.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{req.option_type} 类型下已存在名称为 '{req.name}' 的配置",
        )

    new_id = outline_option_repository.create(
        conn,
        option_type=req.option_type,
        name=req.name,
        description=req.description,
        sort_order=req.sort_order,
        enabled=req.enabled,
    )

    return success_response(data={"id": new_id}, message="新增成功")


@router.put("/story-outline-options/{option_id}")
def update_outline_option(
    option_id: int,
    req: OutlineOptionUpdate,
    current_user: dict = Depends(require_admin_or_root),
    conn: Connection = Depends(get_db),
):
    """修改大纲配置（需要 ADMIN 或 ROOT 权限）"""
    # 检查记录是否存在
    existing = outline_option_repository.find_by_id(conn, option_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )

    # 如果修改了名称，校验唯一性
    if req.name is not None and req.name != existing["name"]:
        duplicate = outline_option_repository.find_by_type_and_name(
            conn, existing["option_type"], req.name
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{existing['option_type']} 类型下已存在名称为 '{req.name}' 的配置",
            )

    outline_option_repository.update(
        conn,
        option_id=option_id,
        name=req.name,
        description=req.description,
        sort_order=req.sort_order,
        enabled=req.enabled,
    )

    return success_response(message="修改成功")


@router.delete("/story-outline-options/{option_id}")
def delete_outline_option(
    option_id: int,
    current_user: dict = Depends(require_admin_or_root),
    conn: Connection = Depends(get_db),
):
    """删除大纲配置（需要 ADMIN 或 ROOT 权限）"""
    existing = outline_option_repository.find_by_id(conn, option_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )

    outline_option_repository.delete_by_id(conn, option_id)
    return success_response(message="删除成功")
