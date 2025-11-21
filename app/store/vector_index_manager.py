"""
向量索引管理器模块
统一管理向量索引操作
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from app.store.exceptions import StoreError
from app.vector.base import VectorSearchBase
from app.embedding import EmbeddingService


logger = logging.getLogger(__name__)


class VectorIndexManager:
    """向量索引管理器 - 统一管理向量索引操作"""
    
    def __init__(self, vector_store: VectorSearchBase, embedding_service: EmbeddingService, executor: ThreadPoolExecutor):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.executor = executor
    
    async def add_to_index(self, content: str, content_id: str, content_type: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """异步添加到向量索引"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._add_to_index_sync,
            content, content_id, content_type, metadata
        )
    
    def _add_to_index_sync(self, content: str, content_id: str, content_type: str,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """同步添加到向量索引"""
        try:
            if self.embedding_service:
                # 确保索引存在
                try:
                    self.vector_store.get_index_info(content_type)
                except Exception:
                    # 索引不存在，创建索引（使用嵌入服务的实际维度）
                    logger.info(f"创建向量索引: {content_type}")
                    # 获取一个测试向量来确定维度
                    test_embedding = self.embedding_service.embed_text("测试")
                    actual_dimension = len(test_embedding)
                    logger.info(f"检测到嵌入维度: {actual_dimension}")
                    self.vector_store.create_index(content_type, dimension=actual_dimension)
                
                embedding = self.embedding_service.embed_text(content, use_cache=True)
                vector_id = f"{content_type}_{content_id}_vec"
                
                # 确保元数据包含内容类型用于过滤
                final_metadata = metadata or {}
                final_metadata['content_type'] = content_type
                
                print(f"DEBUG: 添加向量到索引: index_name='{content_type}', vector_id='{vector_id}', metadata={final_metadata}")
                
                success = self.vector_store.add_vectors(
                    index_name=content_type,
                    vectors=[embedding],
                    ids=[vector_id],
                    metadatas=[final_metadata],
                    texts=[content]
                )
                if success:
                    logger.debug(f"成功添加向量到索引: {content_id} -> {vector_id}")
                    return vector_id
                else:
                    raise StoreError("向量添加失败")
            else:
                return f"{content_type}_{content_id}_vec"
        except Exception as e:
            logger.error(f"添加到向量索引失败: {e}")
            raise StoreError(f"向量索引添加失败: {str(e)}")
    
    async def search_vectors(self, query: str, content_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """异步搜索向量"""
        try:
            if not self.vector_store or not self.embedding_service:
                raise ValueError("向量存储或嵌入服务未初始化")
            
            # 生成查询向量
            print(f"DEBUG: 生成查询向量: query='{query}', content_type='{content_type}'")
            query_embedding = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.embedding_service.embed_text,
                query,
                True  # use_cache
            )
            print(f"DEBUG: 查询向量生成完成: 维度={len(query_embedding) if query_embedding else 0}")
            
            # 搜索相似向量
            print(f"DEBUG: 开始向量搜索: content_type='{content_type}', top_k={limit}")
            results = await self.vector_store.search_vectors_async(
                query_embedding=query_embedding,
                content_type=content_type,
                top_k=limit
            )
            print(f"DEBUG: 向量搜索完成: 返回结果数量={len(results)}")
            
            return results
            
        except Exception as e:
            logger.error(f"异步搜索向量失败: {e}")
            raise StoreError(f"异步搜索向量失败: {str(e)}")
    
    def search_vectors_sync(self, query: str, content_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """同步搜索向量"""
        try:
            if not self.vector_store or not self.embedding_service:
                raise ValueError("向量存储或嵌入服务未初始化")
            
            # 生成查询向量
            query_embedding = self.embedding_service.embed_text(query, use_cache=True)
            
            # 搜索相似向量
            results = self.vector_store.search_vectors_sync(
                query_embedding=query_embedding,
                content_type=content_type,
                top_k=limit
            )
            
            return results
            
        except Exception as e:
            logger.error(f"同步搜索向量失败: {e}")
            raise StoreError(f"同步搜索向量失败: {str(e)}")
    
    async def search_by_embedding(self, embedding: List[float], content_type: Optional[str] = None,
                                 top_k: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """基于嵌入向量的异步搜索"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._search_by_embedding_sync,
            embedding, content_type, top_k, filter_dict
        )
    
    def _search_by_embedding_sync(self, embedding: List[float], content_type: Optional[str] = None,
                                 top_k: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """基于嵌入向量的同步搜索"""
        try:
            if self.vector_store:
                results = self.vector_store.search_similar(
                    query_vector=embedding,
                    top_k=top_k,
                    filter_dict=filter_dict
                )
                if content_type:
                    results = [r for r in results if r.get('content_type') == content_type]
                return results
            else:
                return []
        except Exception as e:
            logger.error(f"基于嵌入的向量搜索失败: {e}")
            raise StoreError(f"基于嵌入的向量搜索失败: {str(e)}")
    
    async def update_vector(self, vector_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """异步更新向量"""
        try:
            if not self.vector_store or not self.embedding_service:
                raise ValueError("向量存储或嵌入服务未初始化")
            
            # 生成新的嵌入向量
            embedding = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.embedding_service.embed_text,
                content,
                True  # use_cache
            )
            
            # 更新向量
            success = await self.vector_store.update_vector_async(
                vector_id=vector_id,
                embedding=embedding,
                metadata=metadata
            )
            
            return success
            
        except Exception as e:
            logger.error(f"异步更新向量失败: {e}")
            raise StoreError(f"异步更新向量失败: {str(e)}")
    
    def update_vector_sync(self, vector_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """同步更新向量"""
        try:
            if not self.vector_store or not self.embedding_service:
                raise ValueError("向量存储或嵌入服务未初始化")
            
            # 生成新的嵌入向量
            embedding = self.embedding_service.embed_text(content, use_cache=True)
            
            # 更新向量
            success = self.vector_store.update_vector_sync(
                vector_id=vector_id,
                embedding=embedding,
                metadata=metadata
            )
            
            return success
            
        except Exception as e:
            logger.error(f"同步更新向量失败: {e}")
            raise StoreError(f"同步更新向量失败: {str(e)}")
    
    async def delete_vector(self, vector_id: str) -> bool:
        """异步删除向量"""
        try:
            if not self.vector_store:
                raise ValueError("向量存储未初始化")
            
            success = await self.vector_store.delete_vector_async(vector_id)
            return success
            
        except Exception as e:
            logger.error(f"异步删除向量失败: {e}")
            raise StoreError(f"异步删除向量失败: {str(e)}")
    
    def delete_vector_sync(self, vector_id: str) -> bool:
        """同步删除向量"""
        try:
            if not self.vector_store:
                raise ValueError("向量存储未初始化")
            
            success = self.vector_store.delete_vector_sync(vector_id)
            return success
            
        except Exception as e:
            logger.error(f"同步删除向量失败: {e}")
            raise StoreError(f"同步删除向量失败: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查向量存储
            if self.vector_store:
                vector_status = self.vector_store.health_check()
            else:
                vector_status = "not_configured"
            
            # 检查嵌入服务
            if self.embedding_service:
                embedding_status = "healthy"
            else:
                embedding_status = "not_configured"
            
            overall_health = vector_status == "healthy" and embedding_status == "healthy"
            
            return {
                "status": "healthy" if overall_health else "unhealthy",
                "vector_store": vector_status,
                "embedding_service": embedding_status,
                "timestamp": "2024-01-01T00:00:00Z"  # 这里应该使用实际的datetime
            }
            
        except Exception as e:
            logger.error(f"向量索引管理器健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }