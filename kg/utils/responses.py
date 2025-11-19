"""
API响应格式统一处理
"""

from typing import Any, Generic, Optional, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """统一API响应格式"""

    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    code: int = Field(200, description="响应状态码")
    timestamp: int = Field(..., description="时间戳")

    class Config:
        pass


def SuccessResponse(
    data: Optional[Any] = None, message: str = "Success", code: int = 200
) -> APIResponse:
    """
    成功响应

    Args:
        data: 响应数据
        message: 响应消息
        code: 响应状态码

    Returns:
        APIResponse
    """
    import time

    return APIResponse(
        success=True, message=message, data=data, code=code, timestamp=int(time.time())
    )


def ErrorResponse(
    message: str = "Error", code: int = 500, data: Optional[Any] = None
) -> APIResponse:
    """
    错误响应

    Args:
        message: 响应消息
        code: 响应状态码
        data: 响应数据

    Returns:
        APIResponse
    """
    import time

    return APIResponse(
        success=False, message=message, data=data, code=code, timestamp=int(time.time())
    )



