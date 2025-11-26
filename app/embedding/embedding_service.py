"""
Embedding 服务
提供文本嵌入的高级服务接口，包括缓存、批处理等功能
"""

import asyncio
import hashlib
import logging
from typing import List, Dict, Any, Optional

from app.config.config_manager import ConfigManager
from .embedding_client import EmbeddingClient
from ..exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding 服务类
    提供文本嵌入的高级功能，包括缓存、批处理、异步处理等
    """
    
    _instance: Optional['EmbeddingService'] = None
    
    def __new__(cls, config_manager: Optional[ConfigManager] = None):
        """
        单例模式实现
        """
        if cls._instance is None:
            if config_manager is None:
                config_manager = ConfigManager()
            cls._instance = super().__new__(cls)
            cls._instance._initialize(config_manager)
        return cls._instance
    
    def _initialize(self, config_manager: ConfigManager):
        """
        初始化服务
        
        Args:
            config_manager: 配置管理器实例
        """
        self._config_manager = config_manager
        self._client = EmbeddingClient(config_manager)
        self._cache_config = config_manager.get_cache_config()
        self._cache: Dict[str, List[float]] = {}
        self._max_cache_size = self._cache_config.max_size
        self._config_manager.add_change_callback(self.refresh)
        logger.info("EmbeddingService 初始化完成")
    
    def _get_text_hash(self, text: str) -> str:
        """
        获取文本的哈希值，用于缓存键
        
        Args:
            text: 输入文本
            
        Returns:
            哈希值字符串
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _manage_cache(self):
        """
        管理缓存大小，防止内存溢出
        """
        if len(self._cache) >= self._max_cache_size:
            # 简单的LRU实现：删除一半的最早缓存项
            items_to_remove = list(self._cache.keys())[:len(self._cache) // 2]
            for key in items_to_remove:
                del self._cache[key]
            logger.debug(f"缓存清理完成，当前缓存大小: {len(self._cache)}")
    
    def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        为单个文本生成嵌入向量
        
        Args:
            text: 要嵌入的文本
            use_cache: 是否使用缓存
            
        Returns:
            嵌入向量
            
        Raises:
            EmbeddingError: 嵌入过程中发生错误
        """
        if not text or not text.strip():
            raise EmbeddingError("输入文本不能为空")
        
        # 检查缓存
        if use_cache:
            text_hash = self._get_text_hash(text)
            if text_hash in self._cache:
                logger.debug("从缓存获取嵌入向量")
                return self._cache[text_hash]
        
        # 生成嵌入向量
        embedding = self._client.embed_text(text)
        
        # 存入缓存
        if use_cache:
            text_hash = self._get_text_hash(text)
            self._cache[text_hash] = embedding
            self._manage_cache()
        
        return embedding
    
    def embed_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        批量为多个文本生成嵌入向量
        
        Args:
            texts: 要嵌入的文本列表
            use_cache: 是否使用缓存
            
        Returns:
            嵌入向量列表
            
        Raises:
            EmbeddingError: 嵌入过程中发生错误
        """
        if not texts:
            raise EmbeddingError("输入文本列表不能为空")
        
        results = []
        uncached_texts = []
        uncached_indices = []
        
        # 检查缓存
        if use_cache:
            for i, text in enumerate(texts):
                if not text or not text.strip():
                    results.append([])
                    continue
                
                text_hash = self._get_text_hash(text)
                if text_hash in self._cache:
                    results.append(self._cache[text_hash])
                else:
                    results.append(None)  # 占位
                    uncached_texts.append(text)
                    uncached_indices.append(i)
            
            # 只对未缓存的文本调用API
            if uncached_texts:
                uncached_embeddings = self._client.embed_batch(uncached_texts)
                
                # 填充结果并更新缓存
                for i, idx in enumerate(uncached_indices):
                    text = uncached_texts[i]
                    embedding = uncached_embeddings[i]
                    results[idx] = embedding
                    
                    text_hash = self._get_text_hash(text)
                    self._cache[text_hash] = embedding
                
                self._manage_cache()
                
        else:
            # 不使用缓存，直接调用API
            valid_texts = []
            valid_indices = []
            
            # 过滤空文本
            for i, text in enumerate(texts):
                if not text or not text.strip():
                    results.append([])
                else:
                    valid_texts.append(text)
                    valid_indices.append(i)
                    results.append(None)  # 占位
            
            # 调用API
            if valid_texts:
                valid_embeddings = self._client.embed_batch(valid_texts)
                
                # 填充结果
                for i, idx in enumerate(valid_indices):
                    results[idx] = valid_embeddings[i]
        
        return results
    
    async def aembed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        异步为单个文本生成嵌入向量
        
        Args:
            text: 要嵌入的文本
            use_cache: 是否使用缓存
            
        Returns:
            嵌入向量
            
        Raises:
            EmbeddingError: 嵌入过程中发生错误
        """
        # 在事件循环中运行同步代码
        return await asyncio.to_thread(self.embed_text, text, use_cache)
    
    async def aembed_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        异步批量为多个文本生成嵌入向量
        
        Args:
            texts: 要嵌入的文本列表
            use_cache: 是否使用缓存
            
        Returns:
            嵌入向量列表
            
        Raises:
            EmbeddingError: 嵌入过程中发生错误
        """
        # 在事件循环中运行同步代码
        return await asyncio.to_thread(self.embed_batch, texts, use_cache)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        计算两个嵌入向量的余弦相似度
        
        Args:
            embedding1: 第一个嵌入向量
            embedding2: 第二个嵌入向量
            
        Returns:
            相似度得分，范围[-1, 1]
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        # 计算点积
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        
        # 计算模长
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5
        
        # 计算余弦相似度
        if norm1 * norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def refresh(self):
        """
        刷新服务配置和客户端
        """
        logger.info("刷新 EmbeddingService 配置")
        self._client.refresh_config()
        self._cache_config = self._config_manager.get_cache_config()
        self._max_cache_size = self._cache_config.max_size
    
    def clear_cache(self):
        """
        清空缓存
        """
        self._cache.clear()
        logger.info("嵌入缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取服务统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'cache_size': len(self._cache),
            'max_cache_size': self._max_cache_size,
            'model': self._client.get_config().get('model', ''),
            'config_manager': self._config_manager.__class__.__name__
        }
