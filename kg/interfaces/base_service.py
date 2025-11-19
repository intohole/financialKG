"""
服务接口基类模块

定义所有服务类共享的接口和通用功能
"""
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseService(ABC):
    """
    服务接口基类
    
    所有服务类都应继承此类，提供统一的初始化、配置和状态管理
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化服务
        
        Args:
            config: 服务配置参数字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._is_initialized = False
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化服务，执行必要的设置操作
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态信息
        
        Returns:
            Dict[str, Any]: 包含服务状态的字典
        """
        return {
            "service_name": self.__class__.__name__,
            "initialized": self._is_initialized,
            "config": self.config
        }
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        更新服务配置
        
        Args:
            config: 新的配置参数字典
        """
        self.config.update(config)
        self.logger.info(f"更新配置: {config}")


class AsyncService(BaseService):
    """
    异步服务接口基类
    
    为异步服务提供统一接口
    """
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        异步初始化服务
        
        Returns:
            bool: 初始化是否成功
        """
        pass


class SingletonMeta(type):
    """
    单例模式元类
    
    确保服务类只有一个实例
    """
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
