"""
存储层异常定义
"""


class StoreError(Exception):
    """存储层基础异常"""
    pass


class EntityNotFoundError(StoreError):
    """实体不存在异常"""
    def __init__(self, entity_id: int):
        self.entity_id = entity_id
        super().__init__(f"实体不存在: {entity_id}")


class RelationNotFoundError(StoreError):
    """关系不存在异常"""
    def __init__(self, relation_id: int):
        self.relation_id = relation_id
        super().__init__(f"关系不存在: {relation_id}")


class VectorStoreError(StoreError):
    """向量存储异常"""
    pass


class MetadataStoreError(StoreError):
    """元数据存储异常"""
    pass


class ValidationError(StoreError):
    """数据验证异常"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message)


class ConnectionError(StoreError):
    """数据库连接异常"""
    pass


class TransactionError(StoreError):
    """事务处理异常"""
    pass