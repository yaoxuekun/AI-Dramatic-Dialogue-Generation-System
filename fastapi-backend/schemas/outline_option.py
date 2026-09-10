from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OutlineOptionCreate(BaseModel):
    """新增大纲配置的请求体"""
    option_type: str = Field(..., description="配置类型：GENRE(题材) 或 STYLE(漫剧风格)", pattern="^(GENRE|STYLE)$")
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")
    sort_order: int = Field(0, ge=0, description="排序序号，越小越靠前")
    enabled: bool = Field(True, description="是否启用")


class OutlineOptionUpdate(BaseModel):
    """修改大纲配置的请求体（所有字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="配置名称")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")
    sort_order: Optional[int] = Field(None, ge=0, description="排序序号")
    enabled: Optional[bool] = Field(None, description="是否启用")


class OutlineOptionResponse(BaseModel):
    """大纲配置的响应体"""
    id: int
    option_type: str
    name: str
    description: Optional[str]
    sort_order: int
    enabled: bool
    created_at: datetime
    updated_at: datetime
