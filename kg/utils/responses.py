"""
API响应格式统一处理
"""

from typing import Dict, Any, Optional, Generic, TypeVar
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    code: int = Field(200, description="响应状态码")
    timestamp: int = Field(..., description="时间戳")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            # 处理datetime对象
            'datetime': lambda v: v.isoformat() if v else None,
            # 处理枚举对象
            'Enum': lambda v: v.value if hasattr(v, 'value') else str(v),
            # 处理TaskExecutionInfo等自定义类
            'TaskExecutionInfo': lambda v: v.to_dict() if hasattr(v, 'to_dict') else v.__dict__
        }


def SuccessResponse(
    data: Optional[Any] = None,
    message: str = "Success",
    code: int = 200
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
        success=True,
        message=message,
        data=data,
        code=code,
        timestamp=int(time.time())
    )


def ErrorResponse(
    message: str = "Error",
    code: int = 500,
    data: Optional[Any] = None
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
        success=False,
        message=message,
        data=data,
        code=code,
        timestamp=int(time.time())
    )


def APIResponseJSON(
    success: bool,
    message: str,
    data: Optional[Any] = None,
    code: int = 200
) -> JSONResponse:
    """
    创建JSON响应
    
    Args:
        success: 是否成功
        message: 响应消息
        data: 响应数据
        code: 响应状态码
        
    Returns:
        JSONResponse
    """
    import time
    response_data = {
        "success": success,
        "message": message,
        "data": data,
        "code": code,
        "timestamp": int(time.time())
    }
    
    return JSONResponse(content=response_data, status_code=code)
