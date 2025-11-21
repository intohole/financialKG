"""
Embedding 异常类
定义嵌入服务相关的各种异常
"""


class EmbeddingError(Exception):
    """
    嵌入服务基础异常类
    所有嵌入服务相关的异常都继承自此类
    """
    pass


class EmbeddingConfigError(EmbeddingError):
    """
    嵌入配置异常
    当嵌入配置无效或缺失时抛出
    """
    pass


class EmbeddingAPIError(EmbeddingError):
    """
    嵌入API异常
    当调用第三方API失败时抛出
    """
    def __init__(self, message: str, error_code: int = None):
        """
        初始化嵌入API异常
        
        Args:
            message: 错误消息
            error_code: API错误代码（如果有）
        """
        super().__init__(message)
        self.error_code = error_code


class EmbeddingTimeoutError(EmbeddingError):
    """
    嵌入超时异常
    当嵌入请求超时时抛出
    """
    pass


class EmbeddingRateLimitError(EmbeddingError):
    """
    嵌入速率限制异常
    当超过API速率限制时抛出
    """
    def __init__(self, message: str, retry_after: int = None):
        """
        初始化嵌入速率限制异常
        
        Args:
            message: 错误消息
            retry_after: 建议的重试等待时间（秒）
        """
        super().__init__(message)
        self.retry_after = retry_after


class EmbeddingValidationError(EmbeddingError):
    """
    嵌入验证异常
    当输入参数验证失败时抛出
    """
    pass
