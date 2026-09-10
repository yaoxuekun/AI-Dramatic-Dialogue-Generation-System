# utils/file_storage.py
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from config import settings

# 允许的文件类型配置
ALLOWED_EXTENSIONS = {
    # 图片
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".svg",
    # 音频
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
    ".flac",
    ".wma",
    # 文档
    ".pdf",
    ".epub",
}

# 最大文件大小（20MB）
MAX_FILE_SIZE = 10 * 1024 * 1024


def get_file_extension(filename: str) -> str:
    "获取文件扩展名（小写）"
    return os.path.splitext(filename)[1].lower()


def validate_file(filename: str, file_size: int) -> None:
    """
    通用文件校验
    :param filename:文件名
    :param file_size:文件大小（字节）
    """
    # 1. 校验扩展名
    ext = get_file_extension(filename)
    if not ext or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式，仅支持: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 2. 校验文件大小
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）",
        )


def generate_file_path(category: str, filename: str) -> str:
    """
    生成文件存储路径
    格式：{category}/{yyyy-MM-dd}/{uuid}.{ext}
    """
    ext = get_file_extension(filename)
    date_str = datetime.now().strftime("%Y-%m-%d")
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join(category, date_str, unique_name)


def save_upload_file(file: UploadFile, category: str = "character-audio") -> str:
    """
    保存上传的音频文件
    :param file: FastAPI UploadFile 对象
    :param category: 存储分类（默认 character-audio）
    :return: 存储的相对路径
    """

    # 1.读取文件内容并校验大小
    content = file.file.read()
    file_size = len(content)
    validate_file(file.filename, file_size)

    # 2.重置文件指针（以便后续操作）
    file.file.seek(0)

    # 3. 生成存储路径
    relative_path = generate_file_path(category, file.filename)
    full_path = os.path.join(settings.STORAGE_ROOT_PATH, relative_path)

    # 4.确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # 5.保存文件
    with open(full_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return relative_path


def delete_file(relative_path: str) -> bool:
    """删除文件（用于更新时清理旧文件）"""
    if not relative_path:
        return False

    full_path = os.path.join(settings.STORAGE_ROOT_PATH, relative_path)
    if os.path.exists(full_path):
        os.remove(full_path)
        return True
    return False


def save_file(file: UploadFile, category: str = "resources") -> dict:
    """
    保存上传文件

    :param file：FastAPI UploadFile对象
    :param category： 存储分类（avatars/resources/covers/generated-assets/character-audio）
    :return：{
        "originalFilename":str,
        "filePath":str, # 相对路径
        "fileUrl":str,  # 访问 URL
        "size":int, # 文件大小（字节）
        "contentType":str   # MIME 类型
    }
    """
    # 1.读取文件内容并校验大小
    content = file.file.read()
    file_size = len(content)
    validate_file(file.filename, file_size)

    # 2.重置文件指针（以便后续操作）
    file.file.seek(0)

    # 3.生成存储路径
    relative_path = generate_file_path(category, file.filename)
    full_path = os.path.join(settings.STORAGE_ROOT_PATH, relative_path)

    # 4. 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # 5.保存文件
    with open(full_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 6.生成访问 URL
    file_url = f"/api/files/{relative_path.replace(os.sep, '/')}"

    return {
        "originalFilename": file.filename,
        "filePath": relative_path,
        "fileUrl": file_url,
        "size": file_size,
        "contentType": file.content_type,
    }


def save_file_from_bytes(
    file_content: bytes, filename: str, category: str = "resources"
) -> dict:
    """
    从字节内容保存文件（用于 AI 生成图片等场景）
    返回格式与 save_file 一致
    """
    file_size = len(file_content)
    validate_file(filename, file_size)

    relative_path = generate_file_path(category, filename)
    full_path = os.path.join(settings.STORAGE_ROOT_PATh, relative_path)

    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "wb") as f:
        f.write(file_content)

    file_url = f"/api/files/{relative_path.replace(os.sep, '/')}"

    return {
        "originalFilename": filename,
        "filePath": relative_path,
        "fileUrl": file_url,
        "size": file_size,
        "contentType": None,
    }


def validate_path_safety(relative_path: str) -> None:
    """
    校验路径安全性，防止路径穿越攻击（如../../../etc/passwd）
    """
    # 1.检查是否包含危险字符
    if ".." in relative_path or "\\" in relative_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="非法的文件路径"
        )
    # 2.规范化路径检查
    normalized = os.path.normpath(relative_path)
    if normalized.startswith("..") or os.path.isabs(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="非法的文件路径"
        )


def get_category_from_path(file_path: str) -> str:
    """从文件路径中提取分类（第一级目录名）"""
    parts = file_path.split(os.sep)
    return parts[0] if parts else "unknown"
