# routers/prompt.py
from fastapi import APIRouter, Depends, HTTPException, status
from pymysql.connections import Connection

from database import get_db
from dependencies import require_admin_or_root
from schemas.common import success_response
from schemas.prompt import PromptCreate, PromptUpdate
from repositories import prompt_repository

router = APIRouter()


@router.get("/prompts")
def get_prompts(
    current_user: dict = Depends(require_admin_or_root),
    conn: Connection = Depends(get_db),
):
    """获取 Prompt 列表（需要 ADMIN 或 ROOT 权限）"""
    prompts = prompt_repository.find_all(conn)
    return success_response(data=prompts, message="获取成功")


@router.get("/prompts/{prompt_id}")
def get_prompt(
    prompt_id: int,
    current_user: dict = Depends(require_admin_or_root),
    conn: Connection = Depends(get_db),
):
    """获取单个 Prompt 详情（需要 ADMIN 或 ROOT 权限）"""
    prompt = prompt_repository.find_by_id(conn, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt 不存在",
        )
    return success_response(data=prompt, message="获取成功")


@router.post("/prompts")
def create_prompt(
    req: PromptCreate,
    current_user: dict = Depends(require_admin_or_root),
    conn: Connection = Depends(get_db),
):
    """新增 Prompt（需要 ADMIN 或 ROOT 权限）"""
    existing = prompt_repository.find_by_prompt_key(conn, req.prompt_key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"prompt_key '{req.prompt_key}' 已存在",
        )

    new_id = prompt_repository.create(
        conn,
        prompt_key=req.prompt_key,
        name=req.name,
        category=req.category,
        description=req.description,
        template_content=req.template_content,
        enabled=req.enabled,
        parameters=[p.model_dump() for p in req.parameters],
        base_prompt_key=req.base_prompt_key,
        prompt_scope=req.prompt_scope,
        match_genre=req.match_genre,
        match_style=req.match_style,
        priority=req.priority,
    )

    return success_response(data={"id": new_id}, message="新增成功")


@router.put("/prompts/{prompt_id}")
def update_prompt(
    prompt_id: int,
    req: PromptUpdate,
    current_user: dict = Depends(require_admin_or_root),
    conn: Connection = Depends(get_db),
):
    """修改 Prompt（需要 ADMIN 或 ROOT 权限）"""
    existing = prompt_repository.find_by_id(conn, prompt_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt 不存在",
        )

    prompt_repository.update(
        conn,
        prompt_id=prompt_id,
        name=req.name,
        category=req.category,
        description=req.description,
        template_content=req.template_content,
        enabled=req.enabled,
        parameters=[p.model_dump() for p in req.parameters] if req.parameters is not None else None,
        base_prompt_key=req.base_prompt_key,
        prompt_scope=req.prompt_scope,
        match_genre=req.match_genre,
        match_style=req.match_style,
        priority=req.priority,
    )

    return success_response(message="修改成功")


@router.delete("/prompts/{prompt_id}")
def delete_prompt(
    prompt_id: int,
    current_user: dict = Depends(require_admin_or_root),
    conn: Connection = Depends(get_db),
):
    """删除 Prompt（需要 ADMIN 或 ROOT 权限）"""
    existing = prompt_repository.find_by_id(conn, prompt_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt 不存在",
        )

    prompt_repository.delete_by_id(conn, prompt_id)
    return success_response(message="删除成功")
