from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FeaturePermissionUpdate(BaseModel):
    """修改功能权限的请求体（所有字段可选）"""
    allowed_roles: Optional[str] = Field(None, max_length=100, description="允许的角色列表，逗号分隔，如 'ADMIN,ROOT,USER'")
    enabled: Optional[bool] = Field(None, description="是否启用")


class FeaturePermissionResponse(BaseModel):
    """功能权限的响应体"""
    id: int
    feature_key: str
    feature_name: str
    category: Optional[str]
    description: Optional[str]
    allowed_roles: str
    enabled: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
