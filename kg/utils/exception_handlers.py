"""
通用异常处理工具
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import traceback
from typing import Any, Optional

from .responses import ErrorResponse, APIResponseJSON


def get_logger() -> logging.Logger:
    """获取配置好的日志记录器"""
    return logging.getLogger(__name__)


def handle_value_error(error: ValueError, logger: Optional[logging.Logger] = None) -> HTTPException:
    """
    处理ValueError异常
    
    Args:
        error: ValueError异常实例
        logger: 日志记录器实例，如果为None则使用默认日志记录器
    
    Returns:
        HTTPException: 400状态码的HTTP异常
    """
    log = logger or get_logger()
    log.warning(f"参数验证错误: {str(error)}")
    return HTTPException(status_code=400, detail=str(error))


def handle_runtime_error(error: RuntimeError, logger: Optional[logging.Logger] = None) -> HTTPException:
    """
    处理RuntimeError异常
    
    Args:
        error: RuntimeError异常实例
        logger: 日志记录器实例，如果为None则使用默认日志记录器
    
    Returns:
        HTTPException: 500状态码的HTTP异常
    """
    log = logger or get_logger()
    log.error(f"运行时错误: {str(error)}")
    return HTTPException(status_code=500, detail=str(error))


def handle_generic_exception(error: Exception, logger: Optional[logging.Logger] = None, context: str = "处理") -> HTTPException:
    """
    处理通用异常
    
    Args:
        error: 异常实例
        logger: 日志记录器实例，如果为None则使用默认日志记录器
        context: 操作上下文描述
    
    Returns:
        HTTPException: 500状态码的HTTP异常
    """
    log = logger or get_logger()
    error_trace = traceback.format_exc()
    log.error(f"{context}过程中发生错误: {str(error)}")
    log.debug(f"异常详情: {error_trace}")
    return HTTPException(status_code=500, detail=f"{context}过程中发生错误: {str(error)}")


async def common_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器，可用于FastAPI的异常处理注册
    
    Args:
        request: FastAPI请求对象
        exc: 异常实例
    
    Returns:
        JSONResponse: 统一格式的错误响应
    """
    logger = get_logger()
    
    # 根据异常类型设置不同的状态码和消息
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        detail = exc.detail
    elif isinstance(exc, ValueError):
        status_code = 400
        detail = str(exc)
    elif isinstance(exc, RuntimeError):
        status_code = 500
        detail = str(exc)
    else:
        status_code = 500
        detail = "服务器内部错误"
        # 记录详细异常栈
        logger.error(f"未处理的异常: {str(exc)}")
        logger.debug(traceback.format_exc())
    
    return APIResponseJSON(
        success=False,
        message=detail,
        code=status_code
    )


def create_api_response_handler():
    """
    创建API响应处理器
    
    Returns:
        Dict[Type[Exception], Callable]: 异常类型到处理器的映射
    """
    return {
        Exception: common_exception_handler
    }
