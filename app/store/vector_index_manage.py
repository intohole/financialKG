"""
向量索引管理器 - 核心向量操作

核心功能：
- 向量添加、更新、删除
- 向量搜索
- 索引管理

设计原则：
- 单一职责：只处理向量相关操作
- 接口简洁：明确定义的API
- 异常处理：统一的异常处理
"""

import logging
from typing import List, Dict, Any, Optional

from app.vector.base import VectorSearchBase
from app.embedding import EmbeddingService
from app.store.store_exceptions_define import StoreError


logger = logging.getLogger(__name__)


class VectorIndexManager:
    """向量索引管理器 - 提供核心向量操作能力"""
    
    def __init__(self, vector_store: VectorSearchBase, 
                 embedding_service: EmbeddingService) -> None:
        """初始化向量索引管理器
        
        Args:
            vector_store: 向量存储实例
            embedding_service: 嵌入服务
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
    
    async def add_to_index(self, content: str, content_id: str, 
                          content_type: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加到向量索引
        
        Args:
            content: 内容文本
            content_id: 内容ID
            content_type: 内容类型（entity, relation, news）
            metadata: 元数据
            
        Returns:
            str: 向量ID
            
        Raises:
            StoreError: 添加失败
        """
        try:
            # 生成嵌入向量
            embedding = await self.embedding_service.embed(content)
            
            # 准备元数据
            if metadata is None:
                metadata = {}
            metadata["content_id"] = str(content_id)
            metadata["content_type"] = content_type
            
            # 添加到向量存储
            vector_id = await self.vector_store.add_vectors(
                texts=[content],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[f"{content_type}_{content_id}"]
            )
            
            logger.debug(f"成功添加向量到索引: {vector_id}")
            return vector_id[0] if isinstance(vector_id, list) else vector_id
            
        except Exception as e:
            logger.error(f"添加到向量索引失败: {e}")
            raise StoreError(f"添加到向量索引失败: {str(e)}")
    
    async def update_vector(self, vector_id: str, content: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新向量
        
        Args:
            vector_id: 向量ID
            content: 新内容
            metadata: 新元数据
            
        Returns:
            bool: 是否成功更新
            
        Raises:
            StoreError: 更新失败
        """
        try:
            # 生成新的嵌入向量
            embedding = await self.embedding_service.embed(content)
            
            # 更新向量
            success = await self.vector_store.update_vector(
                vector_id, content, embedding, metadata
            )
            
            logger.debug(f"成功更新向量: {vector_id}")
            return success
            
        except Exception as e:
            logger.error(f"更新向量失败: {e}")
            raise StoreError(f"更新向量失败: {str(e)}")
    
    async def delete_vector(self, vector_id: str) -> bool:
        """删除向量
        
        Args:
            vector_id: 向量ID
            
        Returns:
            bool: 是否成功删除
            
        Raises:
            StoreError: 删除失败
        """
        try:
            success = await self.vector_store.delete_vectors([vector_id])
            logger.debug(f"成功删除向量: {vector_id}")
            return success
            
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            raise StoreError(f"删除向量失败: {str(e)}")
    
    async def search_vectors(self, query: str, 
                           content_type: Optional[str] = None,
                           top_k: int = 10,
                           filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """搜索向量
        
        Args:
            query: 查询文本
            content_type: 内容类型过滤
            top_k: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
            
        Raises:
            StoreError: 搜索失败
        """
        try:
            # 生成查询向量
            query_embedding = await self.embedding_service.embed(query)
            
            # 准备过滤条件
            where_clause = {}
            if content_type:
                where_clause["content_type"] = content_type
            if filter_dict:
                where_clause.update(filter_dict)
            
            # 执行向量搜索
            results = await self.vector_store.search(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause if where_clause else None
            )
            
            # 格式化结果
            formatted_results = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results.get("metadatas", [{}])[0][i] if results.get("metadatas") else {}
                    distance = results.get("distances", [[0]])[0][i] if results.get("distances") else 0
                    
                    # 将距离转换为相似度分数
                    score = 1.0 - distance
                    
                    formatted_results.append({
                        "content": doc,
                        "score": score,
                        "metadata": metadata,
                        "vector_id": results.get("ids", [[""]])[0][i] if results.get("ids") else ""
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise StoreError(f"向量搜索失败: {str(e)}")
    
    async def get_vector_count(self, content_type: Optional[str] = None) -> int:
        """获取向量数量
        
        Args:
            content_type: 内容类型过滤
            
        Returns:
            int: 向量数量
            
        Raises:
            StoreError: 获取失败
        """
        try:
            filter_dict = {}
            if content_type:
                filter_dict["content_type"] = content_type
            
            return await self.vector_store.count(filter_dict if filter_dict else None)
            
        except Exception as e:
            logger.error(f"获取向量数量失败: {e}")
            raise StoreError(f"获取向量数量失败: {str(e)}")