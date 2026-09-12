from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OutlineOptionCreate(BaseModel):
    """新增大纲配置的请求体"""
    type: str = Field(..., alias="option_type", description="配置类型：GENRE(题材) 或 STYLE(漫剧风格)")
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")
    sortOrder: int = Field(0, alias="sort_order", ge=0, description="排序序号")
    enabled: bool = Field(True, description="是否启用")

    class Config:
        populate_by_name = True


class OutlineOptionUpdate(BaseModel):
    """修改大纲配置的请求体（所有字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="配置名称")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")
    sortOrder: Optional[int] = Field(None, alias="sort_order", ge=0, description="排序序号")
    enabled: Optional[bool] = Field(None, description="是否启用")

    class Config:
        populate_by_name = True


class OutlineOptionResponse(BaseModel):
    """大纲配置的响应体"""
    id: int
    type: str = Field(..., alias="option_type")
    name: str
    description: Optional[str]
    sortOrder: int = Field(..., alias="sort_order")
    enabled: bool
    createdAt: datetime = Field(..., alias="created_at")
    updatedAt: datetime = Field(..., alias="updated_at")

    class Config:
        populate_by_name = True
