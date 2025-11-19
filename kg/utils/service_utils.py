"""
服务工具模块

提供服务初始化、配置管理等通用功能
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
import time
from functools import wraps
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# 定义类型变量
T = TypeVar('T')


class ServiceRegistry:
    """
    服务注册表
    
    管理和维护应用程序中的所有服务实例
    """
    
    def __init__(self):
        """
        初始化服务注册表
        """
        self._services: Dict[str, Any] = {}
        self._initialized: bool = False
    
    def register(self, service_name: str, service_instance: Any) -> None:
        """
        注册服务
        
        Args:
            service_name: 服务名称
            service_instance: 服务实例
        """
        try:
            self._services[service_name] = service_instance
            logger.info(f"服务注册成功: {service_name}")
        except Exception as e:
            logger.error(f"注册服务失败 {service_name}: {str(e)}")
            raise RuntimeError(f"注册服务失败 {service_name}: {str(e)}")
    
    def get(self, service_name: str) -> Any:
        """
        获取服务实例
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务实例
            
        Raises:
            KeyError: 当服务不存在时
        """
        if service_name not in self._services:
            raise KeyError(f"服务未找到: {service_name}")
        return self._services[service_name]
    
    def has(self, service_name: str) -> bool:
        """
        检查服务是否已注册
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 服务是否已注册
        """
        return service_name in self._services
    
    def list_services(self) -> List[str]:
        """
        列出所有注册的服务
        
        Returns:
            List[str]: 服务名称列表
        """
        return list(self._services.keys())
    
    def clear(self) -> None:
        """
        清除所有注册的服务
        """
        self._services.clear()
        self._initialized = False
        logger.info("服务注册表已清空")
    
    async def initialize_all(self) -> bool:
        """
        初始化所有服务
        
        Returns:
            bool: 是否全部初始化成功
        """
        try:
            results = await asyncio.gather(
                *[self._initialize_service(name, service)
                  for name, service in self._services.items()],
                return_exceptions=True
            )
            
            # 检查是否有初始化失败的服务
            success = True
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    service_name = list(self._services.keys())[i]
                    logger.error(f"服务 {service_name} 初始化失败: {str(result)}")
                    success = False
            
            self._initialized = success
            return success
        
        except Exception as e:
            logger.error(f"初始化所有服务时发生错误: {str(e)}")
            return False
    
    async def _initialize_service(self, service_name: str, service: Any) -> bool:
        """
        初始化单个服务
        
        Args:
            service_name: 服务名称
            service: 服务实例
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            if hasattr(service, 'initialize'):
                if asyncio.iscoroutinefunction(service.initialize):
                    result = await service.initialize()
                else:
                    # 如果不是异步方法，在执行器中运行
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(None, service.initialize)
                
                if result:
                    logger.info(f"服务初始化成功: {service_name}")
                else:
                    logger.error(f"服务初始化返回失败: {service_name}")
                
                return result
            
            logger.warning(f"服务 {service_name} 没有initialize方法")
            return True
        
        except Exception as e:
            logger.error(f"服务 {service_name} 初始化异常: {str(e)}")
            raise


# 创建全局服务注册表实例
global_service_registry = ServiceRegistry()


def get_service(service_name: str) -> Any:
    """
    获取全局服务注册表中的服务
    
    Args:
        service_name: 服务名称
        
    Returns:
        服务实例
        
    Raises:
        KeyError: 当服务不存在时
    """
    return global_service_registry.get(service_name)


def register_service(service_name: str, service_instance: Any) -> None:
    """
    注册服务到全局服务注册表
    
    Args:
        service_name: 服务名称
        service_instance: 服务实例
    """
    global_service_registry.register(service_name, service_instance)


def create_service_factory(service_class: type, **default_config) -> Callable[..., Any]:
    """
    创建服务工厂函数
    
    Args:
        service_class: 服务类
        **default_config: 默认配置参数
        
    Returns:
        Callable[..., Any]: 服务工厂函数
    """
    def factory(config: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        # 合并配置
        merged_config = default_config.copy()
        if config:
            merged_config.update(config)
        merged_config.update(kwargs)
        
        # 创建服务实例
        return service_class(merged_config)
    
    return factory


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 需要重试的异常类型
        
    Returns:
        Callable: 装饰后的函数
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"操作失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))  # 指数退避
            
            logger.error(f"所有重试都失败了: {str(last_exception)}")
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"操作失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # 指数退避
            
            logger.error(f"所有重试都失败了: {str(last_exception)}")
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def service_lifecycle(service_factory: Callable[..., Any], **config):
    """
    服务生命周期上下文管理器
    
    Args:
        service_factory: 服务工厂函数
        **config: 服务配置
        
    Yields:
        服务实例
    """
    service = None
    try:
        # 创建服务实例
        service = service_factory(**config)
        
        # 初始化服务
        if hasattr(service, 'initialize'):
            if asyncio.iscoroutinefunction(service.initialize):
                await service.initialize()
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, service.initialize)
        
        yield service
    
    finally:
        # 清理服务资源
        if service and hasattr(service, 'close'):
            try:
                if asyncio.iscoroutinefunction(service.close):
                    await service.close()
                else:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, service.close)
            except Exception as e:
                logger.error(f"关闭服务时发生错误: {str(e)}")


def validate_service_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    验证服务配置
    
    Args:
        config: 配置字典
        required_keys: 必需的配置键列表
        
    Returns:
        bool: 配置是否有效
    """
    try:
        if not isinstance(config, dict):
            logger.error("配置必须是字典类型")
            return False
        
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            logger.error(f"缺少必需的配置键: {missing_keys}")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"验证服务配置时发生错误: {str(e)}")
        return False
