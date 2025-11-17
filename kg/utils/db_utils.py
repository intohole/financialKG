"""
数据库工具模块

提供数据库相关的工具函数和装饰器
"""
import logging
import inspect
from typing import Any, Callable, Optional
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError

# 配置日志
logger = logging.getLogger(__name__)


def handle_db_errors(default_return: Any = None, log_error: bool = True):
    """
    数据库操作异常处理装饰器
    
    Args:
        default_return: 发生异常时的默认返回值
        log_error: 是否记录错误日志
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except SQLAlchemyError as e:
                if log_error:
                    # 尝试从函数参数中获取有用的上下文信息
                    context_parts = []
                    
                    # 添加函数名
                    context_parts.append(f"函数: {func.__name__}")
                    
                    # 添加有意义的参数
                    if args:
                        # 第一个参数通常是self，跳过
                        for i, arg in enumerate(args[1:], 1):
                            if isinstance(arg, (str, int, float)):
                                context_parts.append(f"参数{i}: {arg}")
                    
                    # 添加关键字参数
                    for key, value in kwargs.items():
                        if isinstance(value, (str, int, float)):
                            context_parts.append(f"{key}: {value}")
                    
                    context = ", ".join(context_parts)
                    logger.error(f"数据库操作失败, {context}, 错误: {e}")
                
                return default_return

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SQLAlchemyError as e:
                if log_error:
                    # 尝试从函数参数中获取有用的上下文信息
                    context_parts = []
                    
                    # 添加函数名
                    context_parts.append(f"函数: {func.__name__}")
                    
                    # 添加有意义的参数
                    if args:
                        # 第一个参数通常是self，跳过
                        for i, arg in enumerate(args[1:], 1):
                            if isinstance(arg, (str, int, float)):
                                context_parts.append(f"参数{i}: {arg}")
                    
                    # 添加关键字参数
                    for key, value in kwargs.items():
                        if isinstance(value, (str, int, float)):
                            context_parts.append(f"{key}: {value}")
                    
                    context = ", ".join(context_parts)
                    logger.error(f"数据库操作失败, {context}, 错误: {e}")
                
                return default_return

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    return decorator


def handle_db_errors_with_reraise():
    """
    数据库操作异常处理装饰器，记录日志后重新抛出异常
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except SQLAlchemyError as e:
                # 尝试从函数参数中获取有用的上下文信息
                context_parts = []
                
                # 添加函数名
                context_parts.append(f"函数: {func.__name__}")
                
                # 添加有意义的参数
                if args:
                    # 第一个参数通常是self，跳过
                    for i, arg in enumerate(args[1:], 1):
                        if isinstance(arg, (str, int, float)):
                            context_parts.append(f"参数{i}: {arg}")
                
                # 添加关键字参数
                for key, value in kwargs.items():
                    if isinstance(value, (str, int, float)):
                        context_parts.append(f"{key}: {value}")
                
                context = ", ".join(context_parts)
                logger.error(f"数据库操作失败, {context}, 错误: {e}")
                
                # 重新抛出异常
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SQLAlchemyError as e:
                # 尝试从函数参数中获取有用的上下文信息
                context_parts = []
                
                # 添加函数名
                context_parts.append(f"函数: {func.__name__}")
                
                # 添加有意义的参数
                if args:
                    # 第一个参数通常是self，跳过
                    for i, arg in enumerate(args[1:], 1):
                        if isinstance(arg, (str, int, float)):
                            context_parts.append(f"参数{i}: {arg}")
                
                # 添加关键字参数
                for key, value in kwargs.items():
                    if isinstance(value, (str, int, float)):
                        context_parts.append(f"{key}: {value}")
                
                context = ", ".join(context_parts)
                logger.error(f"数据库操作失败, {context}, 错误: {e}")
                
                # 重新抛出异常
                raise

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    return decorator