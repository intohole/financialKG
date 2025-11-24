"""
服务配置和异常处理模块

提供核心服务层的统一配置管理和异常处理机制，
确保服务的稳定性和可维护性。
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Type, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class ServiceErrorCode(Enum):
    """服务错误码"""
    SUCCESS = "SUCCESS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class ServiceError:
    """服务错误信息"""
    code: ServiceErrorCode
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    service_name: str
    operation: str
    recoverable: bool = True
    retry_count: int = 0
    max_retries: int = 3


class ServiceException(Exception):
    """服务层异常基类"""
    
    def __init__(
        self,
        error_code: ServiceErrorCode,
        message: str,
        service_name: str = "unknown",
        operation: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        original_exception: Optional[Exception] = None
    ):
        self.error = ServiceError(
            code=error_code,
            message=message,
            details=details or {},
            timestamp=datetime.now(),
            service_name=service_name,
            operation=operation,
            recoverable=recoverable
        )
        self.original_exception = original_exception
        super().__init__(message)
    
    def __str__(self):
        return (f"ServiceException[{self.error.code.value}]: "
               f"{self.error.message} (service: {self.error.service_name}, "
               f"operation: {self.error.operation})")


class ValidationException(ServiceException):
    """验证异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            ServiceErrorCode.VALIDATION_ERROR,
            message,
            details=details,
            recoverable=False
        )


class ProcessingException(ServiceException):
    """处理异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(
            ServiceErrorCode.PROCESSING_ERROR,
            message,
            details=details,
            recoverable=True,
            original_exception=original_exception
        )


class StorageException(ServiceException):
    """存储异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(
            ServiceErrorCode.STORAGE_ERROR,
            message,
            details=details,
            recoverable=True,
            original_exception=original_exception
        )


class TimeoutException(ServiceException):
    """超时异常"""
    def __init__(self, message: str, timeout_seconds: float, operation: str):
        super().__init__(
            ServiceErrorCode.TIMEOUT_ERROR,
            message,
            operation=operation,
            details={'timeout_seconds': timeout_seconds},
            recoverable=True
        )


class DependencyException(ServiceException):
    """依赖异常"""
    def __init__(self, dependency_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            ServiceErrorCode.DEPENDENCY_ERROR,
            f"依赖服务 '{dependency_name}' 异常: {message}",
            details=details,
            recoverable=True
        )


class ConfigurationException(ServiceException):
    """配置异常"""
    def __init__(self, config_key: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            ServiceErrorCode.CONFIGURATION_ERROR,
            f"配置项 '{config_key}' 异常: {message}",
            details=details,
            recoverable=False
        )


@dataclass
class ServiceConfig:
    """服务配置"""
    # 超时配置
    default_timeout: float = 30.0
    long_operation_timeout: float = 300.0
    
    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True
    
    # 批处理配置
    default_batch_size: int = 100
    max_batch_size: int = 1000
    batch_timeout: float = 60.0
    
    # 并发配置
    max_concurrent_operations: int = 10
    semaphore_timeout: float = 30.0
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: float = 3600.0  # 1小时
    cache_max_size: int = 1000
    
    # 日志配置
    log_level: str = "INFO"
    log_operation_timing: bool = True
    log_detailed_errors: bool = True
    
    # 质量配置
    min_validation_score: float = 0.7
    max_quality_issues: int = 5
    quality_assessment_enabled: bool = True
    
    # 存储配置
    storage_retry_count: int = 3
    storage_retry_delay: float = 0.5
    storage_health_check_interval: float = 60.0


class ServiceConfigManager:
    """服务配置管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._service_config: Optional[ServiceConfig] = None
        self._config_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}\n        
        logger.info("服务配置管理器初始化完成")
    
    def get_service_config(self) -> ServiceConfig:
        """获取服务配置"""
        if self._service_config is None:
            self._service_config = self._load_service_config()
        return self._service_config
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        try:
            # 检查缓存
            if key in self._config_cache:
                cache_time = self._cache_timestamps.get(key)
                if cache_time and (datetime.now() - cache_time).seconds < 300:  # 5分钟缓存
                    return self._config_cache[key]
            
            # 从配置管理器获取
            value = self.config_manager.get(key, default)
            
            # 缓存结果
            self._config_cache[key] = value
            self._cache_timestamps[key] = datetime.now()
            
            return value
            
        except Exception as e:
            logger.error(f"获取配置值失败: {key}, 错误: {str(e)}")
            return default
    
    def _load_service_config(self) -> ServiceConfig:
        """加载服务配置"""
        try:
            config = ServiceConfig()
            
            # 超时配置
            config.default_timeout = float(self.get_config_value('service.timeout.default', 30.0))
            config.long_operation_timeout = float(self.get_config_value('service.timeout.long_operation', 300.0))
            
            # 重试配置
            config.max_retries = int(self.get_config_value('service.retry.max_retries', 3))
            config.retry_delay = float(self.get_config_value('service.retry.delay', 1.0))
            config.exponential_backoff = bool(self.get_config_value('service.retry.exponential_backoff', True))
            
            # 批处理配置
            config.default_batch_size = int(self.get_config_value('service.batch.default_size', 100))
            config.max_batch_size = int(self.get_config_value('service.batch.max_size', 1000))
            config.batch_timeout = float(self.get_config_value('service.batch.timeout', 60.0))
            
            # 并发配置
            config.max_concurrent_operations = int(self.get_config_value('service.concurrency.max_operations', 10))
            config.semaphore_timeout = float(self.get_config_value('service.concurrency.semaphore_timeout', 30.0))
            
            # 缓存配置
            config.cache_enabled = bool(self.get_config_value('service.cache.enabled', True))
            config.cache_ttl = float(self.get_config_value('service.cache.ttl', 3600.0))
            config.cache_max_size = int(self.get_config_value('service.cache.max_size', 1000))
            
            # 日志配置
            config.log_level = str(self.get_config_value('service.log.level', 'INFO'))
            config.log_operation_timing = bool(self.get_config_value('service.log.operation_timing', True))
            config.log_detailed_errors = bool(self.get_config_value('service.log.detailed_errors', True))
            
            # 质量配置
            config.min_validation_score = float(self.get_config_value('service.quality.min_score', 0.7))
            config.max_quality_issues = int(self.get_config_value('service.quality.max_issues', 5))
            config.quality_assessment_enabled = bool(self.get_config_value('service.quality.assessment_enabled', True))
            
            # 存储配置
            config.storage_retry_count = int(self.get_config_value('service.storage.retry_count', 3))
            config.storage_retry_delay = float(self.get_config_value('service.storage.retry_delay', 0.5))
            config.storage_health_check_interval = float(self.get_config_value('service.storage.health_check_interval', 60.0))
            
            logger.info("服务配置加载完成")
            return config
            
        except Exception as e:
            logger.error(f"加载服务配置失败: {str(e)}")
            return ServiceConfig()  # 返回默认配置
    
    def refresh_config(self) -> None:
        """刷新配置"""
        self._service_config = None
        self._config_cache.clear()
        self._cache_timestamps.clear()
        logger.info("服务配置已刷新")


class ServiceErrorHandler:
    """服务错误处理器"""
    
    def __init__(self, config_manager: ServiceConfigManager):
        self.config_manager = config_manager
        self.error_log: List[ServiceError] = []
        self.max_error_log_size = 1000
        
        logger.info("服务错误处理器初始化完成")
    
    def handle_error(self, exception: ServiceException) -> Dict[str, Any]:
        """处理服务异常"""
        error_info = {
            'error_code': exception.error.code.value,
            'message': exception.error.message,
            'service': exception.error.service_name,
            'operation': exception.error.operation,
            'timestamp': exception.error.timestamp.isoformat(),
            'recoverable': exception.error.recoverable
        }
        
        # 记录错误日志
        self._log_error(exception.error)
        
        # 详细错误信息
        if exception.error.details:
            error_info['details'] = exception.error.details
        
        # 原始异常信息
        if exception.original_exception and exception.error.code != ServiceErrorCode.UNKNOWN_ERROR:
            error_info['original_error'] = str(exception.original_exception)
        
        # 记录详细错误日志
        if self.config_manager.get_service_config().log_detailed_errors:
            logger.error(f"服务异常: {error_info}", exc_info=True)
        else:
            logger.error(f"服务异常: {error_info['message']} "
                        f"({error_info['service']}.{error_info['operation']})")
        
        return error_info
    
    def _log_error(self, error: ServiceError) -> None:
        """记录错误"""
        self.error_log.append(error)
        
        # 限制错误日志大小
        if len(self.error_log) > self.max_error_log_size:
            self.error_log.pop(0)
    
    def get_error_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """获取错误统计"""
        cutoff_time = datetime.now().timestamp() - (time_window_hours * 3600)
        
        recent_errors = [
            error for error in self.error_log
            if error.timestamp.timestamp() > cutoff_time
        ]
        
        # 按错误码统计
        error_code_counts = {}
        for error in recent_errors:
            code = error.code.value
            error_code_counts[code] = error_code_counts.get(code, 0) + 1
        
        # 按服务统计
        service_counts = {}
        for error in recent_errors:
            service = error.service_name
            service_counts[service] = service_counts.get(service, 0) + 1
        
        return {
            'total_errors': len(recent_errors),
            'error_code_distribution': error_code_counts,
            'service_distribution': service_counts,
            'time_window_hours': time_window_hours,
            'most_frequent_error': max(error_code_counts.items(), key=lambda x: x[1])[0] if error_code_counts else None
        }
    
    def clear_error_log(self) -> None:
        """清空错误日志"""
        self.error_log.clear()
        logger.info("错误日志已清空")


def retry_operation(
    max_retries: int = 3,
    delay: float = 1.0,
    exponential_backoff: bool = True,
    exceptions: tuple = (Exception,)
):
    """重试装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        # 计算延迟时间
                        if exponential_backoff:
                            current_delay = delay * (2 ** attempt)
                        else:
                            current_delay = delay
                        
                        logger.warning(f"操作失败，{current_delay}秒后重试 "
                                     f"(尝试 {attempt + 1}/{max_retries}): {str(e)}")
                        
                        await asyncio.sleep(current_delay)
                    else:
                        logger.error(f"操作最终失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            
            # 所有重试都失败
            if last_exception:
                raise last_exception
            else:
                raise Exception("未知错误")
        
        return wrapper
    return decorator


def timeout_operation(timeout_seconds: float):
    """超时装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                raise TimeoutException(
                    f"操作超时 ({timeout_seconds}秒)",
                    timeout_seconds,
                    func.__name__
                )
        
        return wrapper
    return decorator