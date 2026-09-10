from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


# 请求模型
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=100, description="密码")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        # 只允许字母、数字、下划线
        if not v.replace("——", "").isalnum():
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    avatar_path: Optional[str] = None

# 响应模型
class UserProfileResponse(BaseModel):
    id:int
    username:str
    email:str
    avatar_path:Optional[str]=None
    role:str
    created_at:datetime

class LoginResponse(BaseModel):
    token:str
    userId:int
    username:str
    email:str
    avatar_path:Optional[str]=None
    role:str


class UserManageResponse(BaseModel):
    """用户管理响应体（不含密码哈希）"""
    id: int
    username: str
    email: str
    avatar_path: Optional[str] = None
    role: str
    created_at: datetime


class UserUpdateRoleRequest(BaseModel):
    """修改用户角色的请求体"""
    role: str = Field(..., description="目标角色：ROOT / ADMIN / USER", pattern="^(ROOT|ADMIN|USER)$")