"""
向量搜索异常类

定义所有向量搜索操作可能抛出的异常类型
"""

from .base_exceptions import BaseException


class VectorSearchError(BaseException):
    """向量搜索基础异常
    
    所有向量搜索相关异常的基类
    """
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="VECTOR_SEARCH_ERROR", **kwargs)


class IndexNotFoundError(VectorSearchError):
    """索引不存在异常
    
    当向量索引不存在时抛出
    """
    def __init__(self, message: str, index_name: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            index_name: 索引名称
            **kwargs: 额外信息
        """
        kwargs['index_name'] = index_name
        super().__init__(message, error_code="INDEX_NOT_FOUND_ERROR", **kwargs)


class DimensionMismatchError(VectorSearchError):
    """维度不匹配异常
    
    当向量维度不匹配时抛出
    """
    def __init__(self, message: str, expected_dim: int = None, actual_dim: int = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            expected_dim: 期望的维度
            actual_dim: 实际的维度
            **kwargs: 额外信息
        """
        kwargs['expected_dim'] = expected_dim
        kwargs['actual_dim'] = actual_dim
        super().__init__(message, error_code="DIMENSION_MISMATCH_ERROR", **kwargs)


class CollectionNotFoundError(VectorSearchError):
    """集合不存在异常
    
    当向量集合不存在时抛出
    """
    def __init__(self, message: str, collection_name: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            collection_name: 集合名称
            **kwargs: 额外信息
        """
        kwargs['collection_name'] = collection_name
        super().__init__(message, error_code="COLLECTION_NOT_FOUND_ERROR", **kwargs)


class InvalidVectorError(VectorSearchError):
    """无效向量异常
    
    当向量数据无效时抛出
    """
    def __init__(self, message: str, vector_id: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            vector_id: 向量ID
            **kwargs: 额外信息
        """
        kwargs['vector_id'] = vector_id
        super().__init__(message, error_code="INVALID_VECTOR_ERROR", **kwargs)


class VectorStoreConnectionError(VectorSearchError):
    """向量存储连接异常
    
    当向量存储连接失败时抛出
    """
    def __init__(self, message: str, store_type: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            store_type: 存储类型
            **kwargs: 额外信息
        """
        kwargs['store_type'] = store_type
        super().__init__(message, error_code="VECTOR_STORE_CONNECTION_ERROR", **kwargs)


class SearchTimeoutError(VectorSearchError):
    """搜索超时异常
    
    当向量搜索操作超时时抛出
    """
    def __init__(self, message: str, timeout_seconds: float = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            timeout_seconds: 超时时间（秒）
            **kwargs: 额外信息
        """
        kwargs['timeout_seconds'] = timeout_seconds
        super().__init__(message, error_code="SEARCH_TIMEOUT_ERROR", **kwargs)


class InsufficientResourcesError(VectorSearchError):
    """资源不足异常
    
    当向量存储资源不足时抛出
    """
    def __init__(self, message: str, required_resources: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            required_resources: 所需资源描述
            **kwargs: 额外信息
        """
        kwargs['required_resources'] = required_resources
        super().__init__(message, error_code="INSUFFICIENT_RESOURCES_ERROR", **kwargs)


class EmbeddingServiceError(VectorSearchError):
    """嵌入服务异常
    
    当嵌入服务调用失败时抛出
    """
    def __init__(self, message: str, service_name: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            service_name: 服务名称
            **kwargs: 额外信息
        """
        kwargs['service_name'] = service_name
        super().__init__(message, error_code="EMBEDDING_SERVICE_ERROR", **kwargs)


class MetadataError(VectorSearchError):
    """元数据异常
    
    当向量元数据操作失败时抛出
    """
    def __init__(self, message: str, metadata_key: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            metadata_key: 元数据键
            **kwargs: 额外信息
        """
        kwargs['metadata_key'] = metadata_key
        super().__init__(message, error_code="METADATA_ERROR", **kwargs)


class BatchOperationError(VectorSearchError):
    """批量操作异常
    
    当批量向量操作失败时抛出
    """
    def __init__(self, message: str, batch_size: int = None, failed_count: int = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            batch_size: 批次大小
            failed_count: 失败数量
            **kwargs: 额外信息
        """
        kwargs['batch_size'] = batch_size
        kwargs['failed_count'] = failed_count
        super().__init__(message, error_code="BATCH_OPERATION_ERROR", **kwargs)


class FilterError(VectorSearchError):
    """过滤异常
    
    当向量搜索过滤条件无效时抛出
    """
    def __init__(self, message: str, filter_condition: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            filter_condition: 过滤条件
            **kwargs: 额外信息
        """
        kwargs['filter_condition'] = filter_condition
        super().__init__(message, error_code="FILTER_ERROR", **kwargs)


class DistanceMetricError(VectorSearchError):
    """距离度量异常
    
    当距离度量方式无效时抛出
    """
    def __init__(self, message: str, metric: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            metric: 距离度量方式
            **kwargs: 额外信息
        """
        kwargs['metric'] = metric
        super().__init__(message, error_code="DISTANCE_METRIC_ERROR", **kwargs)


class VectorIndexError(VectorSearchError):
    """向量索引异常
    
    当向量索引操作失败时抛出
    """
    def __init__(self, message: str, operation: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            operation: 操作类型
            **kwargs: 额外信息
        """
        kwargs['operation'] = operation
        super().__init__(message, error_code="VECTOR_INDEX_ERROR", **kwargs)


class OptimizationError(VectorSearchError):
    """优化异常
    
    当向量搜索优化失败时抛出
    """
    def __init__(self, message: str, optimization_type: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            optimization_type: 优化类型
            **kwargs: 额外信息
        """
        kwargs['optimization_type'] = optimization_type
        super().__init__(message, error_code="OPTIMIZATION_ERROR", **kwargs)


class IndexAlreadyExistsError(VectorSearchError):

    def __init__(self, message: str, index_name: str = None, **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            index_name: 索引名称
            **kwargs: 额外信息
        """
        kwargs['index_name'] = index_name
        super().__init__(message, error_code="INDEX_ALREADY_EXISTS_ERROR", **kwargs)


class VectorNotFoundError(VectorSearchError):

    def __init__(self, message: str, vector_id: str = None, **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            vector_id: 向量ID
            **kwargs: 额外信息
        """
        kwargs['vector_id'] = vector_id
        super().__init__(message, error_code="VECTOR_NOT_FOUND_ERROR", **kwargs)


class VectorSearchConnectionError(VectorSearchError):

    def __init__(self, message: str, **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="VECTOR_SEARCH_CONNECTION_ERROR", **kwargs)


class VectorSearchTimeoutError(VectorSearchError):


    def __init__(self, message: str, **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="VECTOR_SEARCH_TIMEOUT_ERROR", **kwargs)


class QueryError(VectorSearchError):


    def __init__(self, message: str, **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="QUERY_ERROR", **kwargs)


class IndexOperationError(VectorIndexError):

    def __init__(self, message: str, operation: str = None, **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            operation: 操作类型
            **kwargs: 额外信息
        """
        kwargs['operation'] = operation
        super().__init__(message, error_code="INDEX_OPERATION_ERROR", **kwargs)


class VectorOperationError(VectorSearchError):

    def __init__(self, message: str, operation: str = None, **kwargs):
        """初始化异常

        Args:
            message: 错误消息
            operation: 操作类型
            **kwargs: 额外信息
        """
        kwargs['operation'] = operation
        super().__init__(message, error_code="VECTOR_OPERATION_ERROR", **kwargs)