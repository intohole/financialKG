"""
数据库异常类

定义所有数据库操作可能抛出的异常类型
"""

from .base_exceptions import BaseException


class DatabaseError(BaseException):
    """数据库操作异常基类"""
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="DATABASE_ERROR", **kwargs)


class NotFoundError(DatabaseError):
    """数据未找到异常"""
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="NOT_FOUND_ERROR", **kwargs)


class IntegrityError(DatabaseError):
    """数据完整性异常"""
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="INTEGRITY_ERROR", **kwargs)


class ConnectionError(DatabaseError):
    """数据库连接异常"""
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="CONNECTION_ERROR", **kwargs)


class TransactionError(DatabaseError):
    """事务处理异常"""
    def __init__(self, message: str, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外信息
        """
        super().__init__(message, error_code="TRANSACTION_ERROR", **kwargs)


class QueryError(DatabaseError):
    """查询异常"""
    def __init__(self, message: str, query: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            query: 相关查询语句
            **kwargs: 额外信息
        """
        kwargs['query'] = query
        super().__init__(message, error_code="QUERY_ERROR", **kwargs)


class MigrationError(DatabaseError):
    """数据库迁移异常"""
    def __init__(self, message: str, migration_name: str = None, **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            migration_name: 迁移名称
            **kwargs: 额外信息
        """
        kwargs['migration_name'] = migration_name
        super().__init__(message, error_code="MIGRATION_ERROR", **kwargs)