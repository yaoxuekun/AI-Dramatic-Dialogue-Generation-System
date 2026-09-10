# schemas/file.py
from pydantic import BaseModel
from typing import Optional


class FileUploadResponse(BaseModel):
    """文件上传响应"""

    original_filename: str
    relative_path: str  # filePath
    file_url: str
    file_size: int  # size
    content_type: Optional[str] = None
