"""
Embedding 模块
提供文本嵌入服务，支持多种大模型API
"""

from .embedding_service import EmbeddingService
from .embedding_client import EmbeddingClient
from .exceptions import EmbeddingError
from .models import EmbeddingRequest, EmbeddingResponse

__all__ = [
    'EmbeddingService',
    'EmbeddingClient', 
    'EmbeddingError',
    'EmbeddingRequest',
    'EmbeddingResponse'
]