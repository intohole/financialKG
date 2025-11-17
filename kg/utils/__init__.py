"""
工具函数模块

提供通用的工具函数和装饰器，用于简化代码实现
"""
import logging
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
        def wrapper(*args, **kwargs):
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
        return wrapper
    return decorator


def handle_db_errors_with_reraise():
    """
    数据库操作异常处理装饰器，记录日志后重新抛出异常
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
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
        return wrapper
    return decorator


def handle_errors(error_types: tuple = (Exception,), default_return: Any = None, log_error: bool = True, 
                 log_message: Optional[str] = None):
    """
    通用异常处理装饰器
    
    Args:
        error_types: 要捕获的异常类型元组
        default_return: 发生异常时的默认返回值
        log_error: 是否记录错误日志
        log_message: 自定义错误日志消息模板，可以使用{func_name}和{error}占位符
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                if log_error:
                    if log_message:
                        message = log_message.format(func_name=func.__name__, error=e)
                        logger.error(message)
                    else:
                        # 默认日志消息
                        context_parts = []
                        context_parts.append(f"函数: {func.__name__}")
                        
                        # 添加有意义的参数
                        if args:
                            for i, arg in enumerate(args[1:], 1):
                                if isinstance(arg, (str, int, float)):
                                    context_parts.append(f"参数{i}: {arg}")
                        
                        # 添加关键字参数
                        for key, value in kwargs.items():
                            if isinstance(value, (str, int, float)):
                                context_parts.append(f"{key}: {value}")
                        
                        context = ", ".join(context_parts)
                        logger.error(f"操作失败, {context}, 错误: {e}")
                
                return default_return
        return wrapper
    return decorator