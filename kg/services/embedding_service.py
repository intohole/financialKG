"""
embedding服务模块
提供文本embedding转换功能，支持多种embedding服务
"""
import logging
from typing import List, Optional
from kg.core.config import EmbeddingConfig
from kg.interfaces.embedding_service import EmbeddingServiceInterface
from kg.interfaces.base_service import AsyncService
from kg.utils import handle_errors, validate_embedding

logger = logging.getLogger(__name__)

class ThirdPartyEmbeddingService(EmbeddingServiceInterface, AsyncService):
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
        self._is_initialized = False
    
    @handle_errors(log_error=True, log_message="获取embedding向量失败: {error}")
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
        
        # 调用嵌入服务
        response = await self.client.embeddings.create(
            input=texts,
            model=self.embedding_config.embedding_model
        )
        
        embeddings = [data.embedding for data in response.data]
        
        # 验证嵌入向量
        for i, embedding in enumerate(embeddings):
            if not validate_embedding(embedding):
                logger.warning(f"嵌入向量 {i} 验证失败")
                
        return embeddings
    
    @handle_errors(log_error=True, log_message="获取单个文本embedding向量失败: {error}")
    async def get_embedding(self, text: str) -> List[float]:
        """
        获取单个文本的embedding向量
        
        Args:
            text: 单个文本
            
        Returns:
            embedding向量
        """
        if not text:
            return []
            
        # 直接调用API获取单个文本的embedding
        response = await self.client.embeddings.create(
            input=[text],
            model=self.embedding_config.embedding_model
        )
        
        if response.data and len(response.data) > 0:
            embedding = response.data[0].embedding
            return embedding if validate_embedding(embedding) else []
        
        return []
    
    @handle_errors(log_error=True, log_message="获取embedding维度失败: {error}")
    def get_dimension(self) -> int:
        """
        获取embedding向量的维度
        
        Returns:
            embedding维度
        """
        return self.embedding_config.embedding_dimension
    
    @handle_errors(log_error=True, log_message="验证embedding向量失败: {error}")
    def is_valid_embedding(self, embedding: List[float]) -> bool:
        """
        验证embedding向量是否有效
        
        Args:
            embedding: 待验证的embedding向量
            
        Returns:
            是否有效
        """
        return validate_embedding(embedding)
        
    @handle_errors(log_error=True, log_message="初始化embedding服务失败: {error}")
    async def initialize(self) -> bool:
        """
        初始化embedding服务
        
        Returns:
            bool: 初始化是否成功
        """
        # 验证客户端是否已正确创建
        if hasattr(self, 'client') and self.client:
            self._is_initialized = True
            logger.info("Embedding服务初始化成功")
            return True
        
        logger.error("Embedding服务初始化失败: 客户端未正确创建")
        return False

@handle_errors(log_error=True, log_message="创建embedding服务实例失败: {error}")
def create_embedding_service(config: Optional[EmbeddingConfig] = None) -> EmbeddingServiceInterface:
    """
    创建embedding服务实例
    
    Args:
        config: 嵌入配置实例
        
    Returns:
        EmbeddingServiceInterface实例
    """
    return ThirdPartyEmbeddingService(config)

# 注册服务
from kg.utils.service_utils import register_service
register_service('embedding', create_embedding_service)
