"""
配置相关异常类

定义所有配置管理可能抛出的异常类型
"""

from .base_exceptions import BaseException


class ConfigError(BaseException):
    """配置基础异常
    
    所有配置相关异常的基类
    """
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)


class ConfigNotFoundError(ConfigError):
    """配置文件未找到异常
    
    当配置文件不存在时抛出
    """
    def __init__(self, message: str, config_path: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            config_path: 配置文件路径
            **kwargs: 额外信息
        """
        kwargs['config_path'] = config_path
        super().__init__(message, error_code="CONFIG_NOT_FOUND_ERROR", **kwargs)


class ConfigFormatError(ConfigError):
    """配置格式错误异常
    
    当配置文件格式无效时抛出
    """
    def __init__(self, message: str, config_file: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            config_file: 配置文件名
            **kwargs: 额外信息
        """
        kwargs['config_file'] = config_file
        super().__init__(message, error_code="CONFIG_FORMAT_ERROR", **kwargs)


class ConfigValidationError(ConfigError):
    """配置验证异常
    
    当配置验证失败时抛出
    """
    def __init__(self, message: str, config_key: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            config_key: 配置键
            **kwargs: 额外信息
        """
        kwargs['config_key'] = config_key
        super().__init__(message, error_code="CONFIG_VALIDATION_ERROR", **kwargs)


class ConfigMissingError(ConfigError):
    """配置缺失异常
    
    当必需配置项缺失时抛出
    """
    def __init__(self, message: str, missing_keys: list = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            missing_keys: 缺失的配置键列表
            **kwargs: 额外信息
        """
        kwargs['missing_keys'] = missing_keys
        super().__init__(message, error_code="CONFIG_MISSING_ERROR", **kwargs)


class ConfigPermissionError(ConfigError):
    """配置权限异常
    
    当配置文件权限不足时抛出
    """
    def __init__(self, message: str, config_path: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            config_path: 配置文件路径
            **kwargs: 额外信息
        """
        kwargs['config_path'] = config_path
        super().__init__(message, error_code="CONFIG_PERMISSION_ERROR", **kwargs)


class ConfigLoadError(ConfigError):
    """配置加载异常
    
    当配置文件加载失败时抛出
    """
    def __init__(self, message: str, config_source: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            config_source: 配置来源
            **kwargs: 额外信息
        """
        kwargs['config_source'] = config_source
        super().__init__(message, error_code="CONFIG_LOAD_ERROR", **kwargs)


class ConfigUpdateError(ConfigError):
    """配置更新异常
    
    当配置更新失败时抛出
    """
    def __init__(self, message: str, config_key: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            config_key: 配置键
            **kwargs: 额外信息
        """
        kwargs['config_key'] = config_key
        super().__init__(message, error_code="CONFIG_UPDATE_ERROR", **kwargs)


class ConfigWatchError(ConfigError):
    """配置监控异常
    
    当配置文件监控失败时抛出
    """
    def __init__(self, message: str, watch_path: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            watch_path: 监控路径
            **kwargs: 额外信息
        """
        kwargs['watch_path'] = watch_path
        super().__init__(message, error_code="CONFIG_WATCH_ERROR", **kwargs)