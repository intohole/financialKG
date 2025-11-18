"""
embedding服务模块
提供文本embedding转换功能，支持多种embedding服务
"""
import logging
from typing import List, Optional
from abc import ABC, abstractmethod
from kg.core.config import EmbeddingConfig

logger = logging.getLogger(__name__)

class EmbeddingService(ABC):
    """
    embedding服务抽象基类
    """
    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        将文本列表转换为embedding向量列表
        
        Args:
            texts: 文本列表
            
        Returns:
            embedding向量列表
        """
        pass

class ThirdPartyEmbeddingService(EmbeddingService):
    """
    第三方embedding服务实现
    """
    def __init__(self, embedding_config: Optional[EmbeddingConfig] = None):
        """
        初始化第三方embedding服务
        
        Args:
            embedding_config: 嵌入配置实例
        """
        self.embedding_config = embedding_config or EmbeddingConfig()
        self.client = self.embedding_config.client
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        获取文本的embedding向量
        
        Args:
            texts: 文本列表
            
        Returns:
            embedding向量列表
        """
        if not texts:
            return []
        
        try:
            # 调用嵌入服务
            response = await self.client.embeddings.create(
                input=texts,
                model=self.embedding_config.embedding_model
            )
            
            embeddings = [data.embedding for data in response.data]
            return embeddings
        except Exception as e:
            logger.error(f"获取embedding失败: {str(e)}")
            raise

def create_embedding_service(config: Optional[EmbeddingConfig] = None) -> EmbeddingService:
    """
    创建embedding服务实例
    
    Args:
        config: 嵌入配置实例
        
    Returns:
        EmbeddingService实例
    """
    return ThirdPartyEmbeddingService(config)
