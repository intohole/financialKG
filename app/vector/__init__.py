"""
向量搜索模块
提供统一的向量搜索接口和基于Chroma的实现
"""

# 导出抽象基类
from app.vector.base import VectorSearchBase

# 导出Chroma实现
from app.vector.chroma_vector_search import ChromaVectorSearch

# 导出服务管理类
from app.vector.vector_service import VectorSearchService

# 导出异常类
from app.vector.exceptions import (
    VectorSearchError,
    IndexNotFoundError,
    DimensionMismatchError,
    VectorSearchConnectionError as ConnectionError,
    QueryError,
    VectorOperationError as InsertionError,
    VectorOperationError as DeletionError,
    VectorOperationError as UpdateError,
    VectorSearchError as ConfigurationError,
    VectorSearchError as AuthenticationError,
    VectorSearchError as RateLimitError,
    VectorSearchTimeoutError as TimeoutError
)

# 版本信息
__version__ = "1.0.0"

# 模块描述
__all__ = [
    # 核心类
    "VectorSearchBase",
    "ChromaVectorSearch",
    "VectorSearchService",
    
    # 异常类
    "VectorSearchError",
    "IndexNotFoundError",
    "DimensionMismatchError",
    "ConnectionError",
    "QueryError",
    "InsertionError",
    "DeletionError",
    "UpdateError",
    "ConfigurationError",
    "AuthenticationError",
    "RateLimitError",
    "TimeoutError"
]

# 模块初始化日志
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
