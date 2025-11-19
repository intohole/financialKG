"""
通用异常处理工具
"""

import logging
import traceback
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse




def get_logger() -> logging.Logger:
    """获取配置好的日志记录器"""
    return logging.getLogger(__name__)


def handle_value_error(
    error: ValueError, logger: Optional[logging.Logger] = None
) -> HTTPException:
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


def handle_generic_exception(
    error: Exception, logger: Optional[logging.Logger] = None, context: str = "处理"
) -> HTTPException:
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
    return HTTPException(
        status_code=500, detail=f"{context}过程中发生错误: {str(error)}"
    )
