"""
服务接口模块

提供统一的服务接口定义，确保系统各部分之间的一致性和可扩展性
"""

from .base_service import AsyncService, BaseService, SingletonMeta
from .deduplication_service import DeduplicationServiceInterface
from .embedding_service import EmbeddingServiceInterface
from .llm_service import LLMServiceInterface
from .news_processing_service import NewsProcessingServiceInterface
from .vector_db_service import VectorDBServiceInterface

__all__ = [
    "BaseService",
    "AsyncService",
    "SingletonMeta",
    "EmbeddingServiceInterface",
    "VectorDBServiceInterface",
    "LLMServiceInterface",
    "DeduplicationServiceInterface",
    "NewsProcessingServiceInterface",
]
