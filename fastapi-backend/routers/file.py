# router/file.py
import os
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
from fastapi.responses import FileResponse
from pymysql.connections import Connection
from typing import Optional

from config import settings
from database import get_db
from dependencies import get_current_user
from schemas.common import success_response
from schemas.file import FileUploadResponse
from utils.file_storage import (
    save_file,
    delete_file,
    validate_path_safety,
    get_category_from_path,
    get_file_extension,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files")


@router.post("/upload")
def upload_file(
    file: UploadFile = File(..., description="上传文件"),
    category: str = "resources",
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """
    上传文件（需认证）
    category 可选值：avatars, resources, covers, generated-assets, character-audio
    """
    # 校验 category 合法性
    allowed_categories = {
        "avatars",
        "resources",
        "covers",
        "generated-assets",
        "character-audio",
    }
    if category not in allowed_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"非法的分类，支持：{','.join(allowed_categories)}",
        )

    try:
        result = save_file(file, category)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件保存失败:{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败：{e}",
        )

    return success_response(
        data=FileUploadResponse(
            original_filename=result["originalFilename"],
            relative_path=result["relative_path"],
            file_url=result["fileUrl"],
            file_size=result["size"],
            content_type=result["contentType"],
        ).model_dump(),
        message="文件上传成功",
    )


@router.get("/files/{file_path:path}")
def get_file(file_path: str):
    """
    访问文件（公开，无需认证）
    用于'<img>'标签、音频播放等场景
    """
    # 1.安全校验
    validate_path_safety(file_path)

    # 2.拼接完整路径
    full_path = os.path.join(settings.STORAGE_ROOT_PATH, file_path)

    # 3.检查文件是否存在
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    # 4.根据扩展名设置 Content-Type
    ext = get_file_extension(file_path)
    media_type_map = {
        # 图片
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".bmp": "image/bmp",
        ".ico": "image/x-icon",
        # 音频
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".wma": "audio/x-ms-wma",
        # 文档
        ".pdf": "application/pdf",
        ".epub": "application/epub+zip",
    }
    media_type = media_type_map.get(ext, "application/octet-stream")

    # 5.返回文件（内联显示，而非下载）
    return FileResponse(
        path=full_path,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline;filename="{os.path.basename(file_path)}"'
        },
    )


@router.delete("/files/{file_path:path}")
def delete_file_endpoint(
    file_path: str,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """删除文件（需认证）"""

    # 1.安全校验
    validate_path_safety(file_path)

    # 2.拼接完整路径
    full_path = os.path.join(settings.STORAGE_ROOT_PATH, file_path)

    # 3.检查文件是否存在
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    # 4.删除文件
    if delete_file(file_path):
        logger.info(f"文件删除成功：{file_path},用户：{current_user['username']}")
        return success_response(data=None, message="文件删除成功")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="文件删除失败"
        )
