"""
核心业务异常类

定义核心业务逻辑可能抛出的异常类型
"""

from .base_exceptions import BaseException


class CoreError(BaseException):
    """核心业务基础异常
    
    所有核心业务相关异常的基类
    """
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="CORE_ERROR", **kwargs)


class ServiceError(CoreError):
    """服务层异常
    
    当服务层逻辑失败时抛出
    """
    def __init__(self, message: str, service_name: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            service_name: 服务名称
            **kwargs: 额外信息
        """
        kwargs['service_name'] = service_name
        super().__init__(message, error_code="SERVICE_ERROR", **kwargs)


class BusinessLogicError(CoreError):
    """业务逻辑异常
    
    当业务逻辑验证失败时抛出
    """
    def __init__(self, message: str, business_rule: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            business_rule: 业务规则
            **kwargs: 额外信息
        """
        kwargs['business_rule'] = business_rule
        super().__init__(message, error_code="BUSINESS_LOGIC_ERROR", **kwargs)


class DataProcessingError(CoreError):
    """数据处理异常
    
    当数据处理失败时抛出
    """
    def __init__(self, message: str, data_source: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            data_source: 数据源
            **kwargs: 额外信息
        """
        kwargs['data_source'] = data_source
        super().__init__(message, error_code="DATA_PROCESSING_ERROR", **kwargs)


class EntityNotFoundError(CoreError):
    """实体未找到异常
    
    当请求的业务实体不存在时抛出
    """
    def __init__(self, message: str, entity_type: str = None, entity_id: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            entity_type: 实体类型
            entity_id: 实体ID
            **kwargs: 额外信息
        """
        kwargs['entity_type'] = entity_type
        kwargs['entity_id'] = entity_id
        super().__init__(message, error_code="ENTITY_NOT_FOUND_ERROR", **kwargs)


class RelationNotFoundError(CoreError):

    def __init__(self, message: str, relation_type: str = None, relation_id: str = None, **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            relation_type: 关系类型
            relation_id: 关系ID
            **kwargs: 额外信息
        """
        kwargs['relation_type'] = relation_type
        kwargs['relation_id'] = relation_id
        super().__init__(message, error_code="RELATION_NOT_FOUND_ERROR", **kwargs)


class EntityConflictError(CoreError):
    """实体冲突异常
    
    当业务实体存在冲突时抛出
    """
    def __init__(self, message: str, entity_type: str = None, conflict_field: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            entity_type: 实体类型
            conflict_field: 冲突字段
            **kwargs: 额外信息
        """
        kwargs['entity_type'] = entity_type
        kwargs['conflict_field'] = conflict_field
        super().__init__(message, error_code="ENTITY_CONFLICT_ERROR", **kwargs)


class OperationNotAllowedError(CoreError):
    """操作不允许异常
    
    当执行的操作不被允许时抛出
    """
    def __init__(self, message: str, operation: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            operation: 操作名称
            **kwargs: 额外信息
        """
        kwargs['operation'] = operation
        super().__init__(message, error_code="OPERATION_NOT_ALLOWED_ERROR", **kwargs)


class StateTransitionError(CoreError):
    """状态转换异常
    
    当业务实体状态转换无效时抛出
    """
    def __init__(self, message: str, from_state: str = None, to_state: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            from_state: 源状态
            to_state: 目标状态
            **kwargs: 额外信息
        """
        kwargs['from_state'] = from_state
        kwargs['to_state'] = to_state
        super().__init__(message, error_code="STATE_TRANSITION_ERROR", **kwargs)


class ResourceExhaustedError(CoreError):
    """资源耗尽异常
    
    当系统资源耗尽时抛出
    """
    def __init__(self, message: str, resource_type: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            resource_type: 资源类型
            **kwargs: 额外信息
        """
        kwargs['resource_type'] = resource_type
        super().__init__(message, error_code="RESOURCE_EXHAUSTED_ERROR", **kwargs)


class TimeoutError(CoreError):
    """超时异常
    
    当业务操作超时时抛出
    """
    def __init__(self, message: str, timeout_seconds: float = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            timeout_seconds: 超时时间（秒）
            **kwargs: 额外信息
        """
        kwargs['timeout_seconds'] = timeout_seconds
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)


class DependencyError(CoreError):
    """依赖异常
    
    当外部依赖失败时抛出
    """
    def __init__(self, message: str, dependency_name: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            dependency_name: 依赖名称
            **kwargs: 额外信息
        """
        kwargs['dependency_name'] = dependency_name
        super().__init__(message, error_code="DEPENDENCY_ERROR", **kwargs)