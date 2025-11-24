"""
HybridStore主模块 - 保持向后兼容
"""

from app.database.manager import DatabaseManager
from app.store.hybrid_store_core_implement import HybridStoreCore
from app.vector.base import VectorSearchBase
from app.embedding import EmbeddingService
from concurrent.futures import ThreadPoolExecutor
from typing import Optional


class HybridStore(HybridStoreCore):
    """HybridStore主类 - 保持向后兼容"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, 
                 vector_store: Optional[VectorSearchBase] = None,
                 embedding_service: Optional[EmbeddingService] = None,
                 executor: Optional[ThreadPoolExecutor] = None):
        """
        初始化HybridStore
        
        为了保持向后兼容，这里接受所有原始参数并传递给核心类
        """
        # 忽略executor参数，因为重构后的核心类不需要它
        super().__init__(
            db_manager=db_manager,
            vector_store=vector_store,
            embedding_service=embedding_service
        )