"""
大模型服务异常类

定义所有大模型服务可能抛出的异常类型
"""

from .base_exceptions import BaseException


class LLMError(BaseException):
    """大模型服务基础异常
    
    所有大模型服务相关异常的基类
    """
    def __init__(self, message: str, error_code: str = "LLM_ERROR", **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            **kwargs: 额外信息
        """
        super().__init__(message, error_code, **kwargs)


class PromptError(LLMError):
    """提示词相关异常
    
    当提示词加载、解析或格式化出错时抛出
    """
    def __init__(self, message: str, prompt_name: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            prompt_name: 提示词名称
            **kwargs: 额外信息
        """
        kwargs['prompt_name'] = prompt_name
        super().__init__(message, error_code="PROMPT_ERROR", **kwargs)


class GenerationError(LLMError):
    """生成内容相关异常
    
    当模型生成内容失败时抛出
    """
    def __init__(self, message: str, model: str = None, attempt: int = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            model: 使用的模型名称
            attempt: 尝试次数
            **kwargs: 额外信息
        """
        kwargs['model'] = model
        kwargs['attempt'] = attempt
        super().__init__(message, error_code="GENERATION_ERROR", **kwargs)


class ConfigurationError(LLMError):
    """配置错误
    
    当配置无效或缺失必要项时抛出
    """
    def __init__(self, message: str, config_key: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            config_key: 相关配置键
            **kwargs: 额外信息
        """
        kwargs['config_key'] = config_key
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)


class RateLimitError(LLMError):
    """速率限制异常
    
    当超出API速率限制时抛出
    """
    def __init__(self, message: str, retry_after: int = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            retry_after: 建议重试时间（秒）
            **kwargs: 额外信息
        """
        kwargs['retry_after'] = retry_after
        super().__init__(message, error_code="RATE_LIMIT_ERROR", **kwargs)


class AuthenticationError(LLMError):
    """认证错误
    
    当API密钥无效或认证失败时抛出
    """
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)


class ServiceUnavailableError(LLMError):
    """服务不可用异常
    
    当大模型服务暂时不可用时抛出
    """
    def __init__(self, message: str, service: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            service: 服务名称
            **kwargs: 额外信息
        """
        kwargs['service'] = service
        super().__init__(message, error_code="SERVICE_UNAVAILABLE_ERROR", **kwargs)