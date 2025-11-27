"""
项目统一日志工具

提供项目级别的统一日志记录功能，包括结构化日志、性能监控、异常追踪等
基于配置文件动态设置日志级别和格式
"""

import functools
import logging
import logging.config
import threading
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Callable




class ProjectLoggerAdapter(logging.LoggerAdapter):
    """项目统一日志适配器
    
    提供增强的日志功能，包括结构化日志、性能监控、上下文追踪等
    """
    
    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        """初始化日志适配器
        
        Args:
            logger: 基础logger实例
            extra: 额外的上下文信息
        """
        self.extra = extra or {}
        super().__init__(logger, self.extra)
    
    def process(self, msg: Any, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """处理日志消息
        
        Args:
            msg: 日志消息
            kwargs: 日志参数
            
        Returns:
            tuple: 处理后的消息和参数
        """
        # 获取额外的上下文信息
        extra = kwargs.get('extra', {})
        
        # 合并默认上下文和本次上下文
        merged_extra = self.extra.copy()
        merged_extra.update(extra)
        
        # 添加时间戳和请求ID（如果存在）
        merged_extra['timestamp'] = datetime.now().isoformat()
        if hasattr(threading.current_thread(), 'request_id'):
            merged_extra['request_id'] = threading.current_thread().request_id
        
        kwargs['extra'] = merged_extra
        
        return msg, kwargs
    
    def log_with_context(self, 
                        level: int,
                        msg: Any,
                        context: Optional[Dict[str, Any]] = None,
                        **kwargs) -> None:
        """带上下文的日志记录
        
        Args:
            level: 日志级别
            msg: 日志消息
            context: 上下文信息
            **kwargs: 其他参数
        """
        extra = kwargs.get('extra', {})
        if context:
            extra.update(context)
        kwargs['extra'] = extra
        self.log(level, msg, **kwargs)
    
    def log_error_with_details(self, 
                             exc: Exception,
                             message: str = "操作失败",
                             context: Optional[Dict[str, Any]] = None,
                             **kwargs) -> None:
        """记录包含异常详情的错误日志
        
        Args:
            exc: 异常对象
            message: 错误消息
            context: 上下文信息
            **kwargs: 其他参数
        """
        error_info = {
            'error_type': type(exc).__name__,
            'error_message': str(exc),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }
        
        # 检查是否是特定模块的异常
        if hasattr(exc, 'error_code'):
            error_info['error_code'] = exc.error_code
        if hasattr(exc, 'extra_info'):
            error_info.update(exc.extra_info)
        
        # 合并上下文
        extra = context or {}
        extra['error_details'] = error_info
        
        self.error(message, extra=extra, **kwargs)
    
    def log_performance(self, 
                       operation: str,
                       duration_ms: float,
                       success: bool = True,
                       context: Optional[Dict[str, Any]] = None,
                       **kwargs) -> None:
        """记录性能日志
        
        Args:
            operation: 操作名称
            duration_ms: 耗时（毫秒）
            success: 是否成功
            context: 上下文信息
            **kwargs: 其他参数
        """
        performance_info = {
            'operation': operation,
            'duration_ms': round(duration_ms, 2),
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        # 合并上下文
        extra = context or {}
        extra['performance'] = performance_info
        
        level = logging.INFO if success else logging.WARNING
        self.log(level, f"性能监控: {operation} 耗时 {duration_ms:.2f}ms", extra=extra, **kwargs)
    
    def log_database_operation(self, 
                             operation: str,
                             table: str,
                             duration_ms: float,
                             rows_affected: Optional[int] = None,
                             success: bool = True,
                             context: Optional[Dict[str, Any]] = None,
                             **kwargs) -> None:
        """记录数据库操作日志
        
        Args:
            operation: 操作类型（select, insert, update, delete）
            table: 表名
            duration_ms: 耗时（毫秒）
            rows_affected: 影响的行数
            success: 是否成功
            context: 上下文信息
            **kwargs: 其他参数
        """
        db_info = {
            'operation': operation,
            'table': table,
            'duration_ms': round(duration_ms, 2),
            'rows_affected': rows_affected,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        # 合并上下文
        extra = context or {}
        extra['database'] = db_info
        
        level = logging.INFO if success else logging.WARNING
        self.log(level, f"数据库操作: {operation} {table} 耗时 {duration_ms:.2f}ms", extra=extra, **kwargs)
    
    def log_llm_operation(self, 
                        model: str,
                        operation: str,
                        tokens_used: Optional[Dict[str, int]] = None,
                        cost: Optional[float] = None,
                        duration_ms: Optional[float] = None,
                        success: bool = True,
                        context: Optional[Dict[str, Any]] = None,
                        **kwargs) -> None:
        """记录大模型操作日志
        
        Args:
            model: 模型名称
            operation: 操作类型
            tokens_used: 使用的令牌数量
            cost: 消耗的费用
            duration_ms: 耗时（毫秒）
            success: 是否成功
            context: 上下文信息
            **kwargs: 其他参数
        """
        llm_info = {
            'model': model,
            'operation': operation,
            'tokens_used': tokens_used,
            'cost': cost,
            'duration_ms': duration_ms,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        # 合并上下文
        extra = context or {}
        extra['llm_operation'] = llm_info
        
        level = logging.INFO if success else logging.WARNING
        cost_info = f", 费用: ${cost:.4f}" if cost else ""
        self.log(level, f"LLM操作: {operation} {model}{cost_info}", extra=extra, **kwargs)
    
    def log_vector_operation(self, 
                           operation: str,
                           collection: str,
                           dimension: Optional[int] = None,
                           duration_ms: Optional[float] = None,
                           success: bool = True,
                           context: Optional[Dict[str, Any]] = None,
                           **kwargs) -> None:
        """记录向量操作日志
        
        Args:
            operation: 操作类型
            collection: 集合名称
            dimension: 向量维度
            duration_ms: 耗时（毫秒）
            success: 是否成功
            context: 上下文信息
            **kwargs: 其他参数
        """
        vector_info = {
            'operation': operation,
            'collection': collection,
            'dimension': dimension,
            'duration_ms': duration_ms,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        # 合并上下文
        extra = context or {}
        extra['vector_operation'] = vector_info
        
        level = logging.INFO if success else logging.WARNING
        self.log(level, f"向量操作: {operation} {collection}", extra=extra, **kwargs)


class LoggingManager:
    """日志管理器
    
    负责整个项目的日志配置和管理
    """
    
    def __init__(self):
        self._config_manager = None
        self._loggers: Dict[str, ProjectLoggerAdapter] = {}
        self._lock = threading.Lock()
        self._initialized = False
    
    def initialize(self, config_manager: 'ConfigManager') -> None:
        """初始化日志管理器
        
        Args:
            config_manager: 配置管理器实例
        """

        with self._lock:
            if self._initialized:
                return
            
            self._config_manager = config_manager
            
            try:
                # 获取日志配置
                logging_config = config_manager.get_logging_config()
                
                # 配置日志系统
                self._setup_logging(logging_config)
                
                self._initialized = True
                
                # 使用基础日志器记录初始化成功（避免循环依赖）
                basic_logger = logging.getLogger(__name__)
                basic_logger.info("日志系统初始化成功")
                
                # 添加配置变更监听（可选，避免阻塞）
                try:
                    config_manager.add_change_callback(self._on_config_change)
                except Exception as e:
                    # 如果添加回调失败，记录警告但不阻止初始化
                    basic_logger.warning(f"添加配置变更监听失败: {e}")
                
            except Exception as e:
                # 如果配置失败，使用默认配置
                print(f"⚠️  日志配置失败，使用默认配置: {e}")
                self._setup_default_logging()
                basic_logger = logging.getLogger(__name__)
                basic_logger.error(f"日志配置失败，使用默认配置: {e}")
                self._initialized = True
    
    def _setup_logging(self, logging_config: Any) -> None:
        """根据配置设置日志系统
        
        Args:
            logging_config: 日志配置对象
        """
        try:
            # 延迟导入 ConfigManager 以避免循环依赖
            from app.config.config_manager import ConfigManager
            
            # 确保日志目录存在
            for handler_name, handler_config in logging_config.handlers.items():
                if 'filename' in handler_config:
                    log_file = Path(handler_config['filename'])
                    log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用dictConfig配置日志
            config_dict = {
                'version': logging_config.version,
                'disable_existing_loggers': logging_config.disable_existing_loggers,
                'formatters': logging_config.formatters,
                'handlers': logging_config.handlers,
                'loggers': logging_config.loggers,
                'root': logging_config.root
            }
            
            logging.config.dictConfig(config_dict)
            
        except Exception as e:
            # 使用基础异常而不是 ConfigError 避免循环依赖
            from app.exceptions.base_exceptions import BaseException
            raise BaseException(f"日志配置错误: {e}", error_code="CONFIGURATION_ERROR")
    
    def _setup_default_logging(self) -> None:
        """设置默认日志配置"""
        # 清空现有配置
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # 添加到根日志器
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.INFO)
    
    def _on_config_change(self) -> None:
        """配置变更回调"""
        try:
            # 重新加载日志配置
            logging_config = self._config_manager.get_logging_config()
            self._setup_logging(logging_config)
            
            logger = self.get_logger(__name__)
            logger.info("日志配置已重新加载")
            
        except Exception as e:
            # 使用基础日志器避免循环依赖问题
            basic_logger = logging.getLogger(__name__)
            basic_logger.error(f"日志配置重载失败: {e}")
    
    def get_logger(self, name: str = __name__, 
                   context: Optional[Dict[str, Any]] = None) -> ProjectLoggerAdapter:
        """获取项目日志器
        
        Args:
            name: 日志器名称
            context: 默认上下文信息
            
        Returns:
            ProjectLoggerAdapter: 日志适配器实例
        """
        with self._lock:
            if name not in self._loggers:
                # 避免循环依赖，使用基础日志器
                if name == __name__ or name.endswith('.logging_utils'):
                    # 对于日志工具自身，使用基础日志器
                    logger = logging.getLogger(name)
                else:
                    logger = logging.getLogger(name)
                self._loggers[name] = ProjectLoggerAdapter(logger, context)
            
            return self._loggers[name]


# 全局日志管理器实例
_logging_manager = LoggingManager()


def initialize_logging(config_manager: 'ConfigManager') -> None:
    """初始化项目日志系统
    
    Args:
        config_manager: 配置管理器实例
    """
    _logging_manager.initialize(config_manager)


def get_logger(name: str = __name__, 
               context: Optional[Dict[str, Any]] = None) -> ProjectLoggerAdapter:
    """获取项目日志器
    
    Args:
        name: 日志器名称
        context: 默认上下文信息
        
    Returns:
        ProjectLoggerAdapter: 日志适配器实例
    """
    return _logging_manager.get_logger(name, context)


def performance_logger(operation_name: str):
    """性能监控装饰器
    
    Args:
        operation_name: 操作名称
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.log_performance(operation_name, duration_ms, success=True)
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.log_performance(operation_name, duration_ms, success=False)
                raise
        
        return wrapper
    return decorator


@contextmanager
def performance_context(operation_name: str, context: Optional[Dict[str, Any]] = None):
    """性能监控上下文管理器
    
    Args:
        operation_name: 操作名称
        context: 上下文信息
    """
    logger = get_logger(__name__)
    start_time = time.time()
    
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        logger.log_performance(operation_name, duration_ms, success=True, context=context)
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.log_performance(operation_name, duration_ms, success=False, context=context)
        raise


def set_request_id(request_id: str) -> None:
    """设置当前线程的请求ID
    
    Args:
        request_id: 请求ID
    """
    threading.current_thread().request_id = request_id


def clear_request_id() -> None:
    """清除当前线程的请求ID"""
    if hasattr(threading.current_thread(), 'request_id'):
        delattr(threading.current_thread(), 'request_id')


# 便捷函数
def log_error_with_details(exc: Exception, message: str = "操作失败", 
                          context: Optional[Dict[str, Any]] = None) -> None:
    """记录错误详情
    
    Args:
        exc: 异常对象
        message: 错误消息
        context: 上下文信息
    """
    logger = get_logger(__name__)
    logger.log_error_with_details(exc, message, context)


def log_database_operation(operation: str, table: str, duration_ms: float,
                          rows_affected: Optional[int] = None, success: bool = True,
                          context: Optional[Dict[str, Any]] = None) -> None:
    """记录数据库操作
    
    Args:
        operation: 操作类型
        table: 表名
        duration_ms: 耗时
        rows_affected: 影响的行数
        success: 是否成功
        context: 上下文信息
    """
    logger = get_logger(__name__)
    logger.log_database_operation(operation, table, duration_ms, rows_affected, success, context)


def log_llm_operation(model: str, operation: str, tokens_used: Optional[Dict[str, int]] = None,
                     cost: Optional[float] = None, duration_ms: Optional[float] = None,
                     success: bool = True, context: Optional[Dict[str, Any]] = None) -> None:
    """记录大模型操作
    
    Args:
        model: 模型名称
        operation: 操作类型
        tokens_used: 使用的令牌数量
        cost: 消耗的费用
        duration_ms: 耗时
        success: 是否成功
        context: 上下文信息
    """
    logger = get_logger(__name__)
    logger.log_llm_operation(model, operation, tokens_used, cost, duration_ms, success, context)


def log_vector_operation(operation: str, collection: str, dimension: Optional[int] = None,
                        duration_ms: Optional[float] = None, success: bool = True,
                        context: Optional[Dict[str, Any]] = None) -> None:
    """记录向量操作
    
    Args:
        operation: 操作类型
        collection: 集合名称
        dimension: 向量维度
        duration_ms: 耗时
        success: 是否成功
        context: 上下文信息
    """
    logger = get_logger(__name__)
    logger.log_vector_operation(operation, collection, dimension, duration_ms, success, context)