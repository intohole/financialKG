
class StoreBaseError(BaseException):
    """大模型服务基础异常

    所有大模型服务相关异常的基类
    """
    def __init__(self, message: str, **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            **kwargs: 额外信息，可包含error_code
        """
        # 检查是否在kwargs中重复传递了error_code
        if 'error_code' in kwargs:
            error_code = kwargs.pop('error_code')
            # 确保不与父类重复传递error_code
            super().__init__(message, **kwargs)
        else:
            # 如果没有通过kwargs传递，则使用默认值
            error_code = "STORE_ERROR"
            super().__init__(message, **kwargs)


class StoreError(StoreBaseError):
    """存储服务基础异常

    所有存储服务相关异常的基类
    """
    def __init__(self, message: str, **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            **kwargs: 额外信息，可包含error_code
        """
        if 'error_code' not in kwargs:
            kwargs['error_code'] = "STORE_ERROR"
        super().__init__(message, **kwargs)