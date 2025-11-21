"""大模型服务日志工具

提供增强的日志记录功能，包括结构化日志、异常详情捕获等
"""

import json
import logging
import traceback
from typing import Any, Dict, Optional, Union
from datetime import datetime


class LLMLoggerAdapter(logging.LoggerAdapter):
    """大模型服务日志适配器
    
    提供结构化日志记录功能，自动添加上下文信息
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
        
        # 添加时间戳
        merged_extra['timestamp'] = datetime.now().isoformat()
        
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
            'traceback': traceback.format_exc()
        }
        
        # 检查是否是LLM相关异常
        if hasattr(exc, 'error_code'):
            error_info['error_code'] = exc.error_code
        if hasattr(exc, 'extra_info'):
            error_info.update(exc.extra_info)
        
        # 合并上下文
        extra = context or {}
        extra['error_details'] = error_info
        
        self.error(message, extra=extra, **kwargs)
    
    def log_llm_request(self, 
                       model: str,
                       prompt_type: str,
                       tokens_count: Optional[int] = None,
                       context: Optional[Dict[str, Any]] = None,
                       **kwargs) -> None:
        """记录LLM请求日志
        
        Args:
            model: 模型名称
            prompt_type: 提示词类型
            tokens_count: 令牌数量
            context: 上下文信息
            **kwargs: 其他参数
        """
        request_info = {
            'model': model,
            'prompt_type': prompt_type,
            'tokens_count': tokens_count
        }
        
        # 合并上下文
        extra = context or {}
        extra['llm_request'] = request_info
        
        self.info(f"LLM请求: {prompt_type}", extra=extra, **kwargs)
    
    def log_llm_response(self, 
                        model: str,
                        response_time: float,
                        tokens_used: Optional[Dict[str, int]] = None,
                        cost: Optional[float] = None,
                        context: Optional[Dict[str, Any]] = None,
                        **kwargs) -> None:
        """记录LLM响应日志
        
        Args:
            model: 模型名称
            response_time: 响应时间（秒）
            tokens_used: 使用的令牌数量
            cost: 消耗的费用
            context: 上下文信息
            **kwargs: 其他参数
        """
        response_info = {
            'model': model,
            'response_time_ms': round(response_time * 1000, 2),
            'tokens_used': tokens_used,
            'cost': cost
        }
        
        # 合并上下文
        extra = context or {}
        extra['llm_response'] = response_info
        
        self.info(
            f"LLM响应: {model}, 耗时: {response_time:.2f}s",
            extra=extra,
            **kwargs
        )


def get_llm_logger(name: str = __name__, 
                  context: Optional[Dict[str, Any]] = None) -> LLMLoggerAdapter:
    """获取大模型服务日志器
    
    Args:
        name: 日志器名称
        context: 默认上下文信息
        
    Returns:
        LLMLoggerAdapter: 日志适配器实例
    """
    logger = logging.getLogger(name)
    return LLMLoggerAdapter(logger, context)


def setup_llm_logging(log_level: str = 'INFO',
                      log_file: Optional[str] = None,
                      structured: bool = True) -> None:
    """设置大模型服务日志配置
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        structured: 是否使用结构化日志
    """
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # 清空现有处理器
    root_logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    
    # 创建格式化器
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器
    
    将日志记录格式化为JSON格式
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录对象
            
        Returns:
            str: JSON格式的日志字符串
        """
        # 基础日志字段
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }
        
        # 添加异常信息（如果有）
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # 添加额外信息
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        # 其他标准属性
        for attr in ['filename', 'lineno', 'funcName', 'module']:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)
        
        return json.dumps(log_data, ensure_ascii=False)