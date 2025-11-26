"""
嵌入服务异常类

定义所有嵌入服务可能抛出的异常类型
"""

from .base_exceptions import BaseException


class EmbeddingError(BaseException):
    """嵌入服务基础异常
    
    所有嵌入服务相关异常的基类
    """
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="EMBEDDING_ERROR", **kwargs)


class EmbeddingConfigError(EmbeddingError):
    """嵌入配置异常
    
    当嵌入配置无效时抛出
    """
    def __init__(self, message: str, config_key: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            config_key: 配置键
            **kwargs: 额外信息
        """
        kwargs['config_key'] = config_key
        super().__init__(message, error_code="EMBEDDING_CONFIG_ERROR", **kwargs)


class EmbeddingAPIError(EmbeddingError):
    """嵌入API异常
    
    当嵌入API调用失败时抛出
    """
    def __init__(self, message: str, api_endpoint: str = None, status_code: int = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            api_endpoint: API端点
            status_code: HTTP状态码
            **kwargs: 额外信息
        """
        kwargs['api_endpoint'] = api_endpoint
        kwargs['status_code'] = status_code
        super().__init__(message, error_code="EMBEDDING_API_ERROR", **kwargs)


class EmbeddingTimeoutError(EmbeddingError):
    """嵌入超时异常
    
    当嵌入操作超时时抛出
    """
    def __init__(self, message: str, timeout_seconds: float = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            timeout_seconds: 超时时间（秒）
            **kwargs: 额外信息
        """
        kwargs['timeout_seconds'] = timeout_seconds
        super().__init__(message, error_code="EMBEDDING_TIMEOUT_ERROR", **kwargs)


class EmbeddingRateLimitError(EmbeddingError):
    """嵌入速率限制异常
    
    当超出嵌入API速率限制时抛出
    """
    def __init__(self, message: str, retry_after: int = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            retry_after: 建议重试时间（秒）
            **kwargs: 额外信息
        """
        kwargs['retry_after'] = retry_after
        super().__init__(message, error_code="EMBEDDING_RATE_LIMIT_ERROR", **kwargs)


class EmbeddingValidationError(EmbeddingError):
    """嵌入验证异常
    
    当嵌入输入数据无效时抛出
    """
    def __init__(self, message: str, input_data: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            input_data: 输入数据
            **kwargs: 额外信息
        """
        kwargs['input_data'] = input_data
        super().__init__(message, error_code="EMBEDDING_VALIDATION_ERROR", **kwargs)


class EmbeddingDimensionError(EmbeddingError):
    """嵌入维度异常
    
    当嵌入维度不匹配时抛出
    """
    def __init__(self, message: str, expected_dim: int = None, actual_dim: int = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            expected_dim: 期望的维度
            actual_dim: 实际的维度
            **kwargs: 额外信息
        """
        kwargs['expected_dim'] = expected_dim
        kwargs['actual_dim'] = actual_dim
        super().__init__(message, error_code="EMBEDDING_DIMENSION_ERROR", **kwargs)


class EmbeddingServiceUnavailableError(EmbeddingError):
    """嵌入服务不可用异常
    
    当嵌入服务暂时不可用时抛出
    """
    def __init__(self, message: str, service_name: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            service_name: 服务名称
            **kwargs: 额外信息
        """
        kwargs['service_name'] = service_name
        super().__init__(message, error_code="EMBEDDING_SERVICE_UNAVAILABLE_ERROR", **kwargs)


class EmbeddingAuthenticationError(EmbeddingError):
    """嵌入认证异常
    
    当嵌入服务认证失败时抛出
    """
    def __init__(self, message: str, auth_type: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            auth_type: 认证类型
            **kwargs: 额外信息
        """
        kwargs['auth_type'] = auth_type
        super().__init__(message, error_code="EMBEDDING_AUTHENTICATION_ERROR", **kwargs)


class EmbeddingQuotaExceededError(EmbeddingError):
    """嵌入配额超限异常
    
    当嵌入服务配额用尽时抛出
    """
    def __init__(self, message: str, quota_limit: int = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            quota_limit: 配额限制
            **kwargs: 额外信息
        """
        kwargs['quota_limit'] = quota_limit
        super().__init__(message, error_code="EMBEDDING_QUOTA_EXCEEDED_ERROR", **kwargs)


class EmbeddingModelError(EmbeddingError):
    """嵌入模型异常
    
    当嵌入模型加载或调用失败时抛出
    """
    def __init__(self, message: str, model_name: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            model_name: 模型名称
            **kwargs: 额外信息
        """
        kwargs['model_name'] = model_name
        super().__init__(message, error_code="EMBEDDING_MODEL_ERROR", **kwargs)