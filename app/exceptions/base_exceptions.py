"""
基础异常类

定义项目中所有异常的基类，提供统一的异常处理接口
"""


class BaseException(Exception):
    """项目基础异常类
    
    所有项目异常的基类，提供统一的错误处理接口
    """
    def __init__(self, message: str, error_code: str = "BASE_ERROR", **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            **kwargs: 额外信息
        """
        self.error_code = error_code
        self.extra_info = kwargs
        super().__init__(message)


class ValidationError(BaseException):
    """数据验证异常
    
    当数据验证失败时抛出
    """
    def __init__(self, message: str, field: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            field: 相关字段
            **kwargs: 额外信息
        """
        kwargs['field'] = field
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)


class ConfigurationError(BaseException):
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


class ServiceUnavailableError(BaseException):
    """服务不可用异常
    
    当服务暂时不可用时抛出
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


class AuthenticationError(BaseException):
    """认证错误
    
    当认证失败或API密钥无效时抛出
    """
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)


class RateLimitError(BaseException):
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


class NotFoundError(BaseException):
    """资源未找到异常
    
    当请求的资源不存在时抛出
    """
    def __init__(self, message: str, resource_id: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            resource_id: 资源ID
            **kwargs: 额外信息
        """
        kwargs['resource_id'] = resource_id
        super().__init__(message, error_code="NOT_FOUND_ERROR", **kwargs)


class IntegrityError(BaseException):
    """数据完整性异常
    
    当数据完整性约束被违反时抛出
    """
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="INTEGRITY_ERROR", **kwargs)


class ConnectionError(BaseException):
    """连接异常
    
    当网络连接或数据库连接失败时抛出
    """
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="CONNECTION_ERROR", **kwargs)


class TimeoutError(BaseException):
    """超时异常
    
    当操作超时时抛出
    """
    def __init__(self, message: str, timeout_value: float = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            timeout_value: 超时时间值
            **kwargs: 额外信息
        """
        kwargs['timeout_value'] = timeout_value
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)