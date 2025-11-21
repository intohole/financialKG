"""
向量搜索模块异常类
定义向量数据库操作过程中可能出现的各种异常
"""


class VectorSearchError(Exception):
    """
    向量搜索基础异常类
    所有向量搜索相关异常的父类
    """
    pass


class IndexNotFoundError(VectorSearchError):
    """
    索引不存在异常
    当尝试操作不存在的索引时抛出
    """
    def __init__(self, index_name: str):
        self.index_name = index_name
        super().__init__(f"索引不存在: {index_name}")


class IndexAlreadyExistsError(VectorSearchError):
    """
    索引已存在异常
    当尝试创建已存在的索引时抛出
    """
    def __init__(self, index_name: str):
        self.index_name = index_name
        super().__init__(f"索引已存在: {index_name}")


class VectorNotFoundError(VectorSearchError):
    """
    向量不存在异常
    当尝试获取不存在的向量时抛出
    """
    def __init__(self, vector_id: str):
        self.vector_id = vector_id
        super().__init__(f"向量不存在: {vector_id}")


class DimensionMismatchError(VectorSearchError):
    """
    向量维度不匹配异常
    当向量维度与索引要求的维度不匹配时抛出
    """
    def __init__(self, expected: int, actual: int):
        self.expected = expected
        self.actual = actual
        super().__init__(f"向量维度不匹配: 期望 {expected}，实际 {actual}")


class InvalidVectorError(VectorSearchError):
    """
    无效向量异常
    当向量数据格式不正确时抛出
    """
    def __init__(self, message: str = "无效的向量数据"):
        super().__init__(message)


class VectorSearchConnectionError(VectorSearchError):
    """
    连接错误异常
    当无法连接到向量数据库时抛出
    """
    def __init__(self, message: str = "无法连接到向量数据库"):
        super().__init__(message)


class VectorSearchTimeoutError(VectorSearchError):
    """
    超时错误异常
    当向量搜索操作超时时抛出
    """
    def __init__(self, message: str = "向量搜索操作超时"):
        super().__init__(message)


class QueryError(VectorSearchError):
    """
    查询错误异常
    当搜索查询格式不正确时抛出
    """
    def __init__(self, message: str = "无效的查询参数"):
        super().__init__(message)


class IndexOperationError(VectorSearchError):
    """
    索引操作错误异常
    当索引操作（创建、删除等）失败时抛出
    """
    def __init__(self, operation: str, index_name: str, error: str):
        self.operation = operation
        self.index_name = index_name
        super().__init__(f"索引操作失败 - {operation} {index_name}: {error}")


class VectorOperationError(VectorSearchError):
    """
    向量操作错误异常
    当向量操作（添加、删除、更新等）失败时抛出
    """
    def __init__(self, operation: str, error: str):
        self.operation = operation
        super().__init__(f"向量操作失败 - {operation}: {error}")


class MetadataError(VectorSearchError):
    """
    元数据错误异常
    当元数据格式不正确时抛出
    """
    def __init__(self, message: str = "无效的元数据格式"):
        super().__init__(message)
