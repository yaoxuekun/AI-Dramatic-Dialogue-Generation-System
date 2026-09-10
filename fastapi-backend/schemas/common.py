from pydantic import BaseModel, Field
from typing import Any, Optional, TypeVar, Generic
import time

# 定义泛型，方便后续扩展
T = TypeVar("T")


class ApiResponse(BaseModel):
    """
    统一响应格式。
    所有接口必须返回此结构。
    """

    code: int = Field(..., description="业务状态码，200表示成功")
    message: str = Field(..., description="提示信息")
    data: Optional[Any] = Field(None, description="相应数据可以是对象、数组或者null")
    timestamp: int = Field(..., description="当前时间戳（毫秒）")  # 毫秒时间戳

    class Config:
        json_schema_extre = {
            "example": {
                "code": 200,
                "message": "成功",
                "data": {"id": 1, "name": "test"},
                "timestamp": 1700000000000,
            }
        }


def success_response(data: Any = None, message: str = "成功") -> ApiResponse:
    """
    快捷方法：返回成功响应（code=200）
    """
    return ApiResponse(
        code=200, message=message, data=data, timestamp=int(time.time() * 1000)
    )


def error_response(
    code: int = 400, message: str = "请求失败", data: Any = None
) -> ApiResponse:
    """快捷方法：返回错误响应（code自定义）"""
    return ApiResponse(
        code=code, message=message, data=data, timestamp=int(time.time() * 1000)
    )


# 常见错误码
class ErrorCode:
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUDN = 404
    INTERNAL_ERROR = 500
    VALIDATION_ERROR = 422
