"""大模型服务错误处理器

提供统一的错误处理机制，支持重试策略、错误转换等功能
"""

import time
import logging
import functools
from typing import Any, Callable, Dict, Optional, Union, Type, List
from dataclasses import dataclass
from app.llm.exceptions import (
    LLMError, GenerationError, ConfigurationError, 
    RateLimitError, AuthenticationError, ServiceUnavailableError,
    PromptError
)
from app.llm.logging_utils import get_llm_logger


logger = get_llm_logger(__name__)


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0  # 基础延迟时间（秒）
    max_delay: float = 10.0  # 最大延迟时间（秒）
    backoff_factor: float = 2.0  # 退避因子
    retry_on_exceptions: List[Type[Exception]] = None
    retry_on_status_codes: List[int] = None
    retry_on_messages: List[str] = None


class ErrorHandler:
    """错误处理器
    
    提供统一的错误处理、重试策略和错误转换功能
    """
    
    def __init__(self, default_retry_config: Optional[RetryConfig] = None):
        """初始化错误处理器
        
        Args:
            default_retry_config: 默认重试配置
        """
        self._default_retry_config = default_retry_config or RetryConfig()
        self._logger = get_llm_logger(__name__)
    
    def handle_error(self, 
                    exc: Exception,
                    context: Optional[Dict[str, Any]] = None) -> LLMError:
        """处理异常，转换为LLMError或其子类
        
        Args:
            exc: 原始异常
            context: 上下文信息
            
        Returns:
            LLMError: 转换后的异常
        """
        context = context or {}
        
        # 如果已经是LLMError，直接返回
        if isinstance(exc, LLMError):
            return exc
        
        # 提取错误信息
        error_message = str(exc)
        error_type = type(exc).__name__
        
        # 根据错误特征分类
        try:
            # 检查认证错误
            if any(keyword in error_message.lower() for keyword in [
                'authentication', 'invalid api key', 'api key', 'permission denied'
            ]):
                return AuthenticationError(
                    f"认证失败: {error_message}",
                    **context
                )
            
            # 检查速率限制错误
            if any(keyword in error_message.lower() for keyword in [
                'rate limit', 'too many requests', 'quota exceeded', 'limit exceeded'
            ]):
                # 尝试提取重试时间
                retry_after = self._extract_retry_after(error_message)
                return RateLimitError(
                    f"速率限制: {error_message}",
                    retry_after=retry_after,
                    **context
                )
            
            # 检查服务不可用错误
            if any(keyword in error_message.lower() for keyword in [
                'service unavailable', 'server error', 'timeout', 'connection refused',
                'network error', 'connection error'
            ]):
                return ServiceUnavailableError(
                    f"服务不可用: {error_message}",
                    service=context.get('service'),
                    **context
                )
            
            # 检查配置错误
            if any(keyword in error_message.lower() for keyword in [
                'config', 'configuration', 'invalid parameter', 'parameter error'
            ]):
                return ConfigurationError(
                    f"配置错误: {error_message}",
                    config_key=context.get('config_key'),
                    **context
                )
            
            # 检查提示词错误
            if any(keyword in error_message.lower() for keyword in [
                'prompt', 'template', 'format', 'missing variable'
            ]):
                return PromptError(
                    f"提示词错误: {error_message}",
                    prompt_name=context.get('prompt_name'),
                    **context
                )
            
            # 默认作为生成错误
            return GenerationError(
                f"生成失败: {error_message}",
                model=context.get('model'),
                attempt=context.get('attempt', 1),
                **context
            )
            
        except Exception as e:
            # 如果错误处理过程中出错，记录并返回通用错误
            self._logger.error(f"错误处理失败: {e}")
            return LLMError(
                f"处理异常时出错: {error_message}",
                original_error_type=error_type,
                **context
            )
    
    def _extract_retry_after(self, error_message: str) -> Optional[int]:
        """从错误消息中提取重试时间
        
        Args:
            error_message: 错误消息
            
        Returns:
            Optional[int]: 重试时间（秒）
        """
        try:
            # 简单的正则匹配逻辑
            import re
            match = re.search(r'retry after (\d+)', error_message.lower())
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return None
    
    def should_retry(self, 
                    exc: Exception,
                    retry_config: Optional[RetryConfig] = None) -> bool:
        """判断是否应该重试
        
        Args:
            exc: 异常
            retry_config: 重试配置
            
        Returns:
            bool: 是否应该重试
        """
        config = retry_config or self._default_retry_config
        
        # 检查异常类型
        if config.retry_on_exceptions:
            for exc_type in config.retry_on_exceptions:
                if isinstance(exc, exc_type):
                    return True
        
        # 检查错误消息
        error_message = str(exc).lower()
        if config.retry_on_messages:
            for message_pattern in config.retry_on_messages:
                if message_pattern.lower() in error_message:
                    return True
        
        # 默认重试的异常类型
        retryable_exceptions = [
            GenerationError,
            RateLimitError,
            ServiceUnavailableError
        ]
        
        return isinstance(exc, tuple(retryable_exceptions))
    
    def get_retry_delay(self, 
                       attempt: int,
                       retry_config: Optional[RetryConfig] = None) -> float:
        """计算重试延迟
        
        Args:
            attempt: 重试次数
            retry_config: 重试配置
            
        Returns:
            float: 延迟时间（秒）
        """
        config = retry_config or self._default_retry_config
        
        # 计算指数退避延迟
        delay = config.base_delay * (config.backoff_factor ** (attempt - 1))
        
        # 确保延迟不超过最大值
        return min(delay, config.max_delay)
    
    def retry(self,
              retry_config: Optional[RetryConfig] = None):
        """重试装饰器
        
        Args:
            retry_config: 重试配置
            
        Returns:
            Callable: 装饰后的函数
        """
        config = retry_config or self._default_retry_config
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                attempt = 0
                last_exception = None
                
                while attempt < config.max_retries:
                    attempt += 1
                    
                    try:
                        self._logger.debug(
                            f"执行函数 {func.__name__}, 尝试 {attempt}/{config.max_retries}"
                        )
                        return func(*args, **kwargs)
                    except Exception as e:
                        # 转换异常
                        llm_exception = self.handle_error(e)
                        last_exception = llm_exception
                        
                        # 判断是否应该重试
                        if self.should_retry(llm_exception, config):
                            delay = self.get_retry_delay(attempt, config)
                            self._logger.warning(
                                f"调用失败 (尝试 {attempt}/{config.max_retries}): {llm_exception}, "
                                f"{delay:.2f}秒后重试"
                            )
                            time.sleep(delay)
                        else:
                            self._logger.error(
                                f"调用失败且不重试: {llm_exception}"
                            )
                            raise llm_exception
                
                # 达到最大重试次数
                self._logger.error(
                    f"调用失败，已达到最大重试次数 {config.max_retries}: {last_exception}"
                )
                raise GenerationError(
                    f"调用失败，已达到最大重试次数 {config.max_retries}",
                    original_error=str(last_exception),
                    max_retries=config.max_retries
                )
            
            return wrapper
        
        return decorator
    
    def catch_and_log(self,
                     fallback_value: Any = None,
                     re_raise: bool = False):
        """异常捕获和日志记录装饰器
        
        Args:
            fallback_value: 失败时的回退值
            re_raise: 是否重新抛出异常
            
        Returns:
            Callable: 装饰后的函数
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # 转换异常
                    llm_exception = self.handle_error(e)
                    
                    # 记录错误
                    self._logger.log_error_with_details(
                        llm_exception,
                        f"函数 {func.__name__} 执行失败",
                        context={
                            'function': func.__name__,
                            'args_count': len(args),
                            'kwargs_keys': list(kwargs.keys())
                        }
                    )
                    
                    # 决定是否重新抛出
                    if re_raise:
                        raise llm_exception
                    
                    # 返回回退值
                    return fallback_value
            
            return wrapper
        
        return decorator
    
    def validate_arguments(self,
                          func: Callable = None,
                          **validators):
        """参数验证装饰器
        
        Args:
            func: 要装饰的函数
            **validators: 参数验证器
            
        Returns:
            Callable: 装饰后的函数
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 获取参数名和值
                arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
                arg_dict = dict(zip(arg_names, args))
                arg_dict.update(kwargs)
                
                # 验证参数
                for param_name, validator in validators.items():
                    if param_name in arg_dict:
                        value = arg_dict[param_name]
                        try:
                            if not validator(value):
                                raise ConfigurationError(
                                    f"参数验证失败: {param_name}={value}"
                                )
                        except Exception as e:
                            raise ConfigurationError(
                                f"参数 {param_name} 验证失败: {e}"
                            )
                
                return func(*args, **kwargs)
            
            return wrapper
        
        if func is None:
            return decorator
        return decorator(func)


# 创建默认错误处理器实例
error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """获取错误处理器实例
    
    Returns:
        ErrorHandler: 错误处理器实例
    """
    return error_handler


def retry_on_llm_error(**kwargs):
    """LLM错误重试装饰器
    
    Args:
        **kwargs: 重试配置参数
        
    Returns:
        Callable: 装饰器
    """
    config = RetryConfig(**kwargs)
    return error_handler.retry(config)


def safe_llm_call(fallback_value: Any = None):
    """安全LLM调用装饰器
    
    Args:
        fallback_value: 失败时的回退值
        
    Returns:
        Callable: 装饰器
    """
    return error_handler.catch_and_log(fallback_value=fallback_value, re_raise=False)