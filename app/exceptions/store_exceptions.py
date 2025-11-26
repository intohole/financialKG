
class StoreBaseError(BaseException):
    """大模型服务基础异常

    所有大模型服务相关异常的基类
    """
    def __init__(self, message: str, error_code: str = "STORE_ERROR", **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            error_code: 错误代码
            **kwargs: 额外信息
        """
        super().__init__(message, error_code, **kwargs)


class StoreError(StoreBaseError):
    """存储服务基础异常

    所有存储服务相关异常的基类
    """
    def __init__(self, message: str, error_code: str = "STORE_ERROR", **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            error_code: 错误代码
            **kwargs: 额外信息
        """
        super().__init__(message, error_code, **kwargs)