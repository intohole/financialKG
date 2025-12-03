"""
基于Chroma远程服务器的向量搜索实现
提供Chroma远程向量数据库的操作接口，使用外部embedding服务
"""

import asyncio
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings

from app.exceptions.vector_exceptions import (
    IndexNotFoundError,
    IndexAlreadyExistsError,
    DimensionMismatchError,
    InvalidVectorError,
    VectorSearchConnectionError,
    VectorStoreConnectionError,
    QueryError,
    IndexOperationError,
    VectorOperationError,
    MetadataError
)
from app.utils.logging_utils import get_logger
from app.vector.vector_search_abstract import VectorSearchBase
from app.embedding.embedding_service import EmbeddingService

logger = get_logger(__name__)


class ChromaRemoteVectorSearch(VectorSearchBase):
    """
    基于Chroma远程服务器的向量搜索实现
    使用外部embedding服务，不依赖Chroma内置的embedding功能
    """

    def __init__(self, **kwargs):
        """
        初始化Chroma远程向量搜索客户端
        
        Args:
            **kwargs:
                host: 远程服务器主机地址 (必需)
                port: 远程服务器端口号 (必需)
                collection_name: 默认集合名称
                metric: 距离度量方式，如 'cosine', 'l2', 'ip'
                timeout: 超时时间（秒）
                auth_provider: 认证提供者
                auth_credentials: 认证凭据
                anonymized_telemetry: 是否启用匿名遥测
                embedding_service: EmbeddingService实例（可选，如果不提供则自动创建）
        """
        try:
            # 必需参数验证
            self.host = kwargs.get('host')
            self.port = kwargs.get('port')
            
            if not self.host or not self.port:
                raise ValueError("远程Chroma服务器需要指定host和port参数")
            
            # 配置参数
            self.metric = kwargs.get('metric', 'cosine')
            self.timeout = kwargs.get('timeout', 30)
            anonymized_telemetry = kwargs.get('anonymized_telemetry', False)
            
            # 创建远程Chroma客户端
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    anonymized_telemetry=anonymized_telemetry,
                    chroma_client_auth_provider=kwargs.get('auth_provider'),
                    chroma_client_auth_credentials=kwargs.get('auth_credentials'),
                )
            )
            
            logger.info(f"连接到远程Chroma服务: {self.host}:{self.port}")
            
            # 获取或创建embedding服务
            self.embedding_service = kwargs.get('embedding_service')
            if not self.embedding_service:
                self.embedding_service = EmbeddingService()
                logger.info("自动创建EmbeddingService实例")
            
            # 存储集合映射
            self.collections = {}
            
        except Exception as e:
            logger.error(f"初始化Chroma远程客户端失败: {str(e)}")
            raise VectorSearchConnectionError(f"无法初始化Chroma远程客户端: {str(e)}")

    def _get_collection(self, index_name: str) -> chromadb.Collection:
        """
        获取或创建集合
        
        Args:
            index_name: 索引名称
            
        Returns:
            chromadb.Collection: 集合对象
            
        Raises:
            IndexNotFoundError: 当集合不存在时
        """
        try:
            if index_name in self.collections:
                return self.collections[index_name]
            
            # 检查集合是否存在
            collections = self.client.list_collections()
            collection_names = [col.name for col in collections]
            
            if index_name in collection_names:
                # 获取现有集合（不指定embedding_function）
                collection = self.client.get_collection(name=index_name)
                self.collections[index_name] = collection
                return collection
            else:
                raise IndexNotFoundError(index_name)
                
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取集合失败: {str(e)}")
            raise VectorStoreConnectionError(f"获取集合失败: {str(e)}")

    def create_index(self, index_name: str, dimension: int, **kwargs) -> bool:
        """
        创建向量索引（Chroma中称为集合）
        
        Args:
            index_name: 索引名称
            dimension: 向量维度
            **kwargs: 其他索引配置参数
                metadata: 索引元数据
                
        Returns:
            bool: 创建是否成功
            
        Raises:
            IndexAlreadyExistsError: 当索引已存在时
        """
        try:
            # 检查索引是否已存在
            collections = self.client.list_collections()
            collection_names = [col.name for col in collections]
            
            if index_name in collection_names:
                raise IndexAlreadyExistsError(index_name)
            
            # 创建集合（不指定embedding_function，使用外部embedding）
            metadata = kwargs.get('metadata', {})
            metadata["hnsw:space"] = kwargs.get('metric', self.metric)
            metadata["dimension"] = dimension
            
            # 创建集合时不提供embedding_function
            self.client.create_collection(
                name=index_name,
                metadata=metadata
            )
            
            logger.info(f"成功创建远程索引: {index_name}，维度: {dimension}")
            return True
            
        except IndexAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"创建远程索引失败: {str(e)}")
            raise IndexOperationError(f"create远程索引操作失败: {str(e)}", operation="create", index_name=index_name)

    def add_vectors(
        self,
        index_name: str,
        vectors: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        texts: Optional[List[str]] = None,
        **kwargs
    ) -> bool:
        """
        向索引中添加向量
        
        Args:
            index_name: 索引名称
            vectors: 向量列表（已生成的向量，不是原始文本）
            ids: 向量ID列表
            metadatas: 元数据列表
            texts: 原始文本列表（可选）
            **kwargs: 其他参数
                
        Returns:
            bool: 添加是否成功
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 验证输入参数
            if len(vectors) != len(ids):
                raise InvalidVectorError("向量和ID数量不匹配")
            
            if metadatas and len(metadatas) != len(vectors):
                raise InvalidVectorError("元数据数量与向量数量不匹配")
            
            # 添加向量到集合
            collection.add(
                embeddings=vectors,
                ids=ids,
                metadatas=metadatas,
                documents=texts
            )
            
            logger.info(f"成功添加 {len(vectors)} 个向量到远程索引: {index_name}")
            return True
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"添加向量到远程索引失败: {str(e)}")
            raise VectorOperationError(f"add向量到远程索引操作失败: {str(e)}", operation="add", index_name=index_name)

    def search_vectors(
        self,
        index_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        搜索相似向量
        
        Args:
            index_name: 索引名称
            query_vector: 查询向量（已生成的向量，不是原始文本）
            top_k: 返回结果数量
            filter_dict: 过滤条件
            **kwargs: 其他搜索参数
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 执行搜索
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=filter_dict,
                include=["metadatas", "documents", "distances"]
            )
            
            # 格式化结果
            formatted_results = []
            
            if results['ids'] and results['ids'][0]:
                for i, vector_id in enumerate(results['ids'][0]):
                    result = {
                        "id": vector_id,
                        "score": 1.0 - results['distances'][0][i] if results['distances'] and results['distances'][0] else 0.0,  # 转换为相似度分数
                        "metadata": results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                    }
                    
                    # 如果有文档内容，也包含在结果中
                    if results['documents'] and results['documents'][0] and i < len(results['documents'][0]):
                        result["text"] = results['documents'][0][i]
                    
                    formatted_results.append(result)
            
            logger.info(f"远程向量搜索完成，索引: {index_name}，返回 {len(formatted_results)} 个结果")
            return formatted_results
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"远程向量搜索失败: {str(e)}")
            raise QueryError(f"远程向量搜索失败: {str(e)}", query=f"index:{index_name}")

    def delete_vectors(self, index_name: str, ids: List[str]) -> bool:
        """
        删除向量
        
        Args:
            index_name: 索引名称
            ids: 要删除的向量ID列表
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 删除向量
            collection.delete(ids=ids)
            
            logger.info(f"成功从远程索引 {index_name} 删除 {len(ids)} 个向量")
            return True
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"从远程索引删除向量失败: {str(e)}")
            raise VectorOperationError(f"delete向量从远程索引操作失败: {str(e)}", operation="delete", index_name=index_name)

    def update_vectors(
        self,
        index_name: str,
        vectors: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        texts: Optional[List[str]] = None,
    ) -> bool:
        """
        更新向量
        
        Args:
            index_name: 索引名称
            vectors: 新向量列表（已生成的向量）
            ids: 向量ID列表
            metadatas: 新元数据列表
            texts: 新原始文本列表
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 验证输入参数
            if len(vectors) != len(ids):
                raise InvalidVectorError("向量和ID数量不匹配")
            
            if metadatas and len(metadatas) != len(vectors):
                raise InvalidVectorError("元数据数量与向量数量不匹配")
            
            # 更新向量
            collection.update(
                embeddings=vectors,
                ids=ids,
                metadatas=metadatas,
                documents=texts
            )
            
            logger.info(f"成功更新远程索引 {index_name} 中的 {len(vectors)} 个向量")
            return True
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"更新远程索引中的向量失败: {str(e)}")
            raise VectorOperationError(f"update向量在远程索引操作失败: {str(e)}", operation="update", index_name=index_name)

    def get_vectors(
        self,
        index_name: str,
        ids: List[str],
        include_vectors: bool = True,
        include_metadatas: bool = True,
        include_texts: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        获取向量信息
        
        Args:
            index_name: 索引名称
            ids: 向量ID列表
            include_vectors: 是否包含向量数据
            include_metadatas: 是否包含元数据
            include_texts: 是否包含原始文本
            
        Returns:
            List[Dict[str, Any]]: 向量信息列表
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 准备include参数
            include_params = []
            if include_metadatas:
                include_params.append("metadatas")
            if include_texts:
                include_params.append("documents")
            if include_vectors:
                include_params.append("embeddings")
            
            # 获取向量信息
            results = collection.get(
                ids=ids,
                include=include_params
            )
            
            # 格式化结果
            formatted_results = []
            
            if results['ids']:
                for i, vector_id in enumerate(results['ids']):
                    result = {"id": vector_id}
                    
                    if include_metadatas and results['metadatas'] and i < len(results['metadatas']):
                        result["metadata"] = results['metadatas'][i]
                    
                    if include_texts and results['documents'] and i < len(results['documents']):
                        result["text"] = results['documents'][i]
                    
                    if include_vectors and results['embeddings'] and i < len(results['embeddings']):
                        result["vector"] = results['embeddings'][i]
                    
                    formatted_results.append(result)
            
            logger.info(f"成功从远程索引 {index_name} 获取 {len(formatted_results)} 个向量信息")
            return formatted_results
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"从远程索引获取向量信息失败: {str(e)}")
            raise VectorOperationError(f"get向量信息从远程索引失败: {str(e)}", operation="get", index_name=index_name)

    def get_index_info(self, index_name: str) -> Dict[str, Any]:
        """
        获取索引信息
        
        Args:
            index_name: 索引名称
            
        Returns:
            Dict[str, Any]: 索引信息
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 获取集合统计信息
            count = collection.count()
            
            info = {
                "name": index_name,
                "count": count,
                "dimension": None,  # Chroma不直接提供维度信息
                "metric": self.metric
            }
            
            # 尝试从元数据获取维度信息
            if hasattr(collection, 'metadata') and collection.metadata:
                info["dimension"] = collection.metadata.get("dimension")
            
            logger.info(f"成功获取远程索引 {index_name} 的信息: {info}")
            return info
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取远程索引信息失败: {str(e)}")
            raise VectorOperationError(f"获取远程索引信息失败: {str(e)}", operation="info", index_name=index_name)

    def list_indices(self) -> List[str]:
        """
        列出所有索引
        
        Returns:
            List[str]: 索引名称列表
        """
        try:
            collections = self.client.list_collections()
            index_names = [col.name for col in collections]
            
            logger.info(f"成功列出 {len(index_names)} 个远程索引")
            return index_names
            
        except Exception as e:
            logger.error(f"列出远程索引失败: {str(e)}")
            raise VectorOperationError(f"列出远程索引失败: {str(e)}", operation="list")

    def delete_index(self, index_name: str) -> bool:
        """
        删除索引
        
        Args:
            index_name: 索引名称
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 检查索引是否存在
            self._get_collection(index_name)
            
            # 删除索引
            self.client.delete_collection(name=index_name)
            
            # 从缓存中移除
            if index_name in self.collections:
                del self.collections[index_name]
            
            logger.info(f"成功删除远程索引: {index_name}")
            return True
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"删除远程索引失败: {str(e)}")
            raise VectorOperationError(f"删除远程索引失败: {str(e)}", operation="delete", index_name=index_name)

    def count_vectors(self, index_name: str) -> int:
        """
        统计索引中的向量数量
        
        Args:
            index_name: 索引名称
            
        Returns:
            int: 向量数量
        """
        try:
            collection = self._get_collection(index_name)
            count = collection.count()
            
            logger.info(f"远程索引 {index_name} 中的向量数量: {count}")
            return count
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"统计远程索引向量数量失败: {str(e)}")
            raise VectorOperationError(f"统计远程索引向量数量失败: {str(e)}", operation="count", index_name=index_name)

    def close(self) -> None:
        """
        关闭连接，释放资源
        """
        try:
            # Chroma HTTP客户端没有显式的close方法
            self.collections.clear()
            logger.info("Chroma远程客户端连接已关闭")
        except Exception as e:
            logger.error(f"关闭Chroma远程客户端连接失败: {str(e)}")

    # ==================== 便捷方法 ====================
    
    def add_texts(
        self,
        index_name: str,
        texts: List[str],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> bool:
        """
        添加文本（自动调用embedding服务生成向量）
        
        Args:
            index_name: 索引名称
            texts: 文本列表
            ids: 文本ID列表
            metadatas: 元数据列表
            **kwargs: 其他参数
                
        Returns:
            bool: 添加是否成功
        """
        try:
            # 批量生成嵌入向量
            embeddings = self.embedding_service.embed_batch(texts)
            
            # 添加向量
            return self.add_vectors(
                index_name=index_name,
                vectors=embeddings,
                ids=ids,
                metadatas=metadatas,
                texts=texts
            )
            
        except Exception as e:
            logger.error(f"添加文本到远程索引失败: {str(e)}")
            raise VectorOperationError(f"添加文本到远程索引失败: {str(e)}", operation="add_texts", index_name=index_name)

    async def aadd_texts(
        self,
        index_name: str,
        texts: List[str],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> bool:
        """
        异步添加文本（自动调用embedding服务生成向量）
        
        Args:
            index_name: 索引名称
            texts: 文本列表
            ids: 文本ID列表
            metadatas: 元数据列表
            **kwargs: 其他参数
                
        Returns:
            bool: 添加是否成功
        """
        try:
            # 异步生成嵌入向量
            embeddings = []
            for text in texts:
                embedding = await self.embedding_service.aembed_text(text)
                embeddings.append(embedding)
            
            # 在事件循环中运行同步添加方法
            return await asyncio.to_thread(
                self.add_vectors,
                index_name=index_name,
                vectors=embeddings,
                ids=ids,
                metadatas=metadatas,
                texts=texts
            )
            
        except Exception as e:
            logger.error(f"异步添加文本到远程索引失败: {str(e)}")
            raise VectorOperationError(f"异步添加文本到远程索引失败: {str(e)}", operation="aadd_texts", index_name=index_name)

    def search_texts(
        self,
        index_name: str,
        query_text: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文本（自动调用embedding服务生成查询向量）
        
        Args:
            index_name: 索引名称
            query_text: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件
            **kwargs: 其他搜索参数
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        try:
            # 生成查询向量
            query_embedding = self.embedding_service.embed_text(query_text)
            
            # 执行向量搜索
            return self.search_vectors(
                index_name=index_name,
                query_vector=query_embedding,
                top_k=top_k,
                filter_dict=filter_dict
            )
            
        except Exception as e:
            logger.error(f"远程文本搜索失败: {str(e)}")
            raise QueryError(f"远程文本搜索失败: {str(e)}", query=query_text)

    async def asearch_texts(
        self,
        index_name: str,
        query_text: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        异步搜索相似文本（自动调用embedding服务生成查询向量）
        
        Args:
            index_name: 索引名称
            query_text: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件
            **kwargs: 其他搜索参数
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        try:
            # 异步生成查询向量
            query_embedding = await self.embedding_service.aembed_text(query_text)
            
            # 在事件循环中运行同步搜索方法
            return await asyncio.to_thread(
                self.search_vectors,
                index_name=index_name,
                query_vector=query_embedding,
                top_k=top_k,
                filter_dict=filter_dict
            )
            
        except Exception as e:
            logger.error(f"异步远程文本搜索失败: {str(e)}")
            raise QueryError(f"异步远程文本搜索失败: {str(e)}", query=query_text)