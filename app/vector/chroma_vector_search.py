"""
基于Chroma的向量搜索实现
提供Chroma向量数据库的操作接口
"""

import asyncio
from pathlib import Path
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

logger = get_logger(__name__)


class ChromaVectorSearch(VectorSearchBase):
    """
    基于Chroma的向量搜索实现
    使用Chroma作为后端存储和检索向量
    """

    def __init__(self, **kwargs):
        """
        初始化Chroma向量搜索客户端
        
        Args:
            **kwargs:
                path: 本地存储路径
                host: 主机地址（如需远程连接）
                port: 端口号
                collection_name: 默认集合名称
                metric: 距离度量方式，如 'cosine', 'l2', 'ip'
                embedding_function: 嵌入函数（可选）
                timeout: 超时时间（秒）
                anonymized_telemetry: 是否启用匿名遥测
        """
        try:
            # 配置参数
            path = kwargs.get('path', './data/chroma')
            host = kwargs.get('host')
            port = kwargs.get('port')
            self.metric = kwargs.get('metric', 'cosine')
            self.timeout = kwargs.get('timeout', 30)
            anonymized_telemetry = kwargs.get('anonymized_telemetry', False)
            
            # 确保路径存在
            if path:
                Path(path).mkdir(parents=True, exist_ok=True)
            
            # 根据参数决定使用本地模式还是远程模式
            if host and port:
                # 远程模式
                self.client = chromadb.HttpClient(
                    host=host,
                    port=port,
                    settings=Settings(
                        anonymized_telemetry=anonymized_telemetry,
                        chroma_client_auth_provider=kwargs.get('auth_provider'),
                        chroma_client_auth_credentials=kwargs.get('auth_credentials'),
                    )
                )
                logger.info(f"连接到远程Chroma服务: {host}:{port}")
            else:
                # 本地模式
                self.client = chromadb.PersistentClient(
                    path=path,
                    settings=Settings(
                        anonymized_telemetry=anonymized_telemetry,
                        is_persistent=True,
                    )
                )
                logger.info(f"初始化本地Chroma客户端，存储路径: {path}")
            
            # 存储集合映射
            self.collections = {}
            
        except Exception as e:
            logger.error(f"初始化Chroma客户端失败: {str(e)}")
            raise VectorSearchConnectionError(f"无法初始化Chroma客户端: {str(e)}")

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
                # 获取现有集合
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
                embedding_function: 嵌入函数
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
            
            # 创建集合
            metadata = kwargs.get('metadata', {})
            metadata["hnsw:space"] = kwargs.get('metric', self.metric)
            metadata["dimension"] = dimension
            
            embedding_function = kwargs.get('embedding_function')
            
            self.client.create_collection(
                name=index_name,
                metadata=metadata,
                embedding_function=embedding_function
            )
            
            logger.info(f"成功创建索引: {index_name}，维度: {dimension}")
            return True
            
        except IndexAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            raise IndexOperationError(f"create操作失败: {str(e)}", operation="create", index_name=index_name)

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
            vectors: 向量列表
            ids: 向量ID列表
            metadatas: 元数据列表
            texts: 原始文本列表
            **kwargs: 其他参数
                embedding_function: 嵌入函数（如果未提供向量时使用）
                
        Returns:
            bool: 添加是否成功
            
        Raises:
            IndexNotFoundError: 当索引不存在时
            DimensionMismatchError: 当向量维度不匹配时
            InvalidVectorError: 当向量数据无效时
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 验证输入参数
            if not vectors:
                raise InvalidVectorError("向量列表不能为空")
            
            if len(vectors) != len(ids):
                raise InvalidVectorError("向量数量与ID数量不匹配")
            
            if metadatas and len(metadatas) != len(ids):
                raise MetadataError("元数据数量与ID数量不匹配")
            
            if texts and len(texts) != len(ids):
                raise InvalidVectorError("文本数量与ID数量不匹配")
            
            # 验证向量维度（从第一个向量获取）
            first_vector_dim = len(vectors[0])
            for i, vector in enumerate(vectors):
                if len(vector) != first_vector_dim:
                    raise InvalidVectorError(f"向量{i}维度不一致")
            
            # 检查索引维度是否匹配（如果有存储）
            if hasattr(collection, 'metadata') and 'dimension' in collection.metadata:
                index_dim = collection.metadata['dimension']
                if first_vector_dim != index_dim:
                    raise DimensionMismatchError(index_dim, first_vector_dim)
            
            # 添加向量
            collection.add(
                embeddings=vectors,
                ids=ids,
                metadatas=metadatas,
                documents=texts
            )
            
            logger.info(f"成功添加 {len(vectors)} 个向量到索引: {index_name}")
            return True
            
        except (IndexNotFoundError, DimensionMismatchError, InvalidVectorError, MetadataError):
            raise
        except Exception as e:
            logger.error(f"添加向量失败: {str(e)}")
            raise VectorOperationError("add", str(e))

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
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_dict: 过滤条件
            **kwargs: 其他搜索参数
                include: 要包含的字段，如 ['embeddings', 'metadatas', 'documents']
                
        Returns:
            List[Dict[str, Any]]: 搜索结果列表，每个结果包含id、向量、元数据、文档、相似度分数等
            
        Raises:
            IndexNotFoundError: 当索引不存在时
            QueryError: 当查询参数无效时
        """
        try:
            logger.debug(f"开始搜索向量: index_name='{index_name}', top_k={top_k}, filter_dict={filter_dict}")
            
            # 获取集合
            collection = self._get_collection(index_name)
            logger.debug(f"获取集合成功: {collection.name}")
            
            # 验证查询向量
            if not query_vector or not isinstance(query_vector, list):
                raise QueryError("无效的查询向量")
            
            logger.debug(f"查询向量验证通过: 维度={len(query_vector)}")
            
            # 设置包含字段
            include = kwargs.get('include', ['embeddings', 'metadatas', 'documents', 'distances'])
            
            # 执行搜索
            logger.debug(f"执行Chroma查询: n_results={top_k}, filter={filter_dict}")
            
            # 构建ChromaDB格式的where条件
            chroma_where = None
            if filter_dict:
                # 如果只有一个条件，直接使用
                if len(filter_dict) == 1:
                    chroma_where = filter_dict
                else:
                    # 多个条件需要使用 $and 操作符
                    chroma_where = {"$and": [{k: v} for k, v in filter_dict.items()]}
            
            logger.debug(f"转换后的Chroma where条件: {chroma_where}")
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=chroma_where,
                include=include
            )
            
            logger.debug(f"Chroma查询完成: results.keys()={list(results.keys())}")
            
            # 检查搜索结果
            if 'ids' not in results or results['ids'] is None or len(results['ids'][0]) == 0:
                logger.debug("搜索结果为空")
                return []
            
            # 格式化结果
            formatted_results = []
            for i in range(len(results['ids'][0])):
                result = {
                    'id': results['ids'][0][i],
                    'score': results['distances'][0][i] if 'distances' in results and results['distances'] is not None else None
                }
                
                if 'embeddings' in results and results['embeddings'] is not None and len(results['embeddings']) > 0 and results['embeddings'][0] is not None:
                    result['vector'] = results['embeddings'][0][i]
                
                if 'metadatas' in results and results['metadatas'] is not None and len(results['metadatas']) > 0 and results['metadatas'][0] is not None:
                    result['metadata'] = results['metadatas'][0][i]
                
                if 'documents' in results and results['documents'] is not None and len(results['documents']) > 0 and results['documents'][0] is not None:
                    result['text'] = results['documents'][0][i]
                
                formatted_results.append(result)
            
            logger.info(f"搜索完成，在索引 {index_name} 中找到 {len(formatted_results)} 个结果")
            return formatted_results
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"搜索向量失败: {str(e)}")
            raise QueryError(f"搜索失败: {str(e)}")

    def delete_vectors(self, index_name: str, ids: List[str]) -> bool:
        """
        删除向量
        
        Args:
            index_name: 索引名称
            ids: 要删除的向量ID列表
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            IndexNotFoundError: 当索引不存在时
            VectorNotFoundError: 当要删除的向量不存在时
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 验证ID列表
            if not ids:
                raise InvalidVectorError("ID列表不能为空")
            
            # 删除向量
            collection.delete(ids=ids)
            
            logger.info(f"成功从索引 {index_name} 删除 {len(ids)} 个向量")
            return True
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"删除向量失败: {str(e)}")
            raise VectorOperationError("delete", str(e))

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
            vectors: 新向量列表
            ids: 向量ID列表
            metadatas: 新元数据列表
            texts: 新原始文本列表
            
        Returns:
            bool: 更新是否成功
            
        Raises:
            IndexNotFoundError: 当索引不存在时
            VectorNotFoundError: 当要更新的向量不存在时
            InvalidVectorError: 当向量数据无效时
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 验证输入参数
            if len(vectors) != len(ids):
                raise InvalidVectorError("向量数量与ID数量不匹配")
            
            if metadatas and len(metadatas) != len(ids):
                raise MetadataError("元数据数量与ID数量不匹配")
            
            if texts and len(texts) != len(ids):
                raise InvalidVectorError("文本数量与ID数量不匹配")
            
            # 更新向量
            collection.update(
                embeddings=vectors,
                ids=ids,
                metadatas=metadatas,
                documents=texts
            )
            
            logger.info(f"成功更新索引 {index_name} 中的 {len(vectors)} 个向量")
            return True
            
        except (IndexNotFoundError, InvalidVectorError, MetadataError):
            raise
        except Exception as e:
            logger.error(f"更新向量失败: {str(e)}")
            raise VectorOperationError("update", str(e))

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
            
        Raises:
            IndexNotFoundError: 当索引不存在时
            VectorNotFoundError: 当向量不存在时
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 构建include参数
            include = []
            if include_vectors:
                include.append('embeddings')
            if include_metadatas:
                include.append('metadatas')
            if include_texts:
                include.append('documents')
            
            # 获取向量
            results = collection.get(
                ids=ids,
                include=include
            )
            
            # 格式化结果
            formatted_results = []
            id_to_index = {vec_id: idx for idx, vec_id in enumerate(results['ids'])}
            
            for vec_id in ids:
                if vec_id not in id_to_index:
                    continue
                
                idx = id_to_index[vec_id]
                result = {'id': vec_id}
                
                if include_vectors and 'embeddings' in results and results['embeddings']:
                    result['vector'] = results['embeddings'][idx]
                
                if include_metadatas and 'metadatas' in results and results['metadatas']:
                    result['metadata'] = results['metadatas'][idx]
                
                if include_texts and 'documents' in results and results['documents']:
                    result['text'] = results['documents'][idx]
                
                formatted_results.append(result)
            
            return formatted_results
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取向量失败: {str(e)}")
            raise VectorOperationError("get", str(e))

    def get_index_info(self, index_name: str) -> Dict[str, Any]:
        """
        获取索引信息
        
        Args:
            index_name: 索引名称
            
        Returns:
            Dict[str, Any]: 索引信息，包括名称、向量数量、维度、元数据等
            
        Raises:
            IndexNotFoundError: 当索引不存在时
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 获取向量数量
            count = self.count_vectors(index_name)
            
            # 构建索引信息
            info = {
                'name': index_name,
                'count': count,
                'metadata': collection.metadata if hasattr(collection, 'metadata') else {},
                'type': 'chroma',
                'metric': self.metric
            }
            
            return info
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取索引信息失败: {str(e)}")
            raise IndexOperationError(f"get_info操作失败: {str(e)}", operation="get_info", index_name=index_name)

    def list_indices(self) -> List[str]:
        """
        列出所有索引
        
        Returns:
            List[str]: 索引名称列表
        """
        try:
            collections = self.client.list_collections()
            index_names = [col.name for col in collections]
            return index_names
            
        except Exception as e:
            logger.error(f"列出索引失败: {str(e)}")
            raise IndexOperationError(f"list操作失败: {str(e)}", operation="list")

    def delete_index(self, index_name: str) -> bool:
        """
        删除索引
        
        Args:
            index_name: 索引名称
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            IndexNotFoundError: 当索引不存在时
        """
        try:
            # 检查索引是否存在
            collections = self.client.list_collections()
            collection_names = [col.name for col in collections]
            
            if index_name not in collection_names:
                raise IndexNotFoundError(index_name)
            
            # 删除索引
            self.client.delete_collection(name=index_name)
            
            # 从缓存中移除
            if index_name in self.collections:
                del self.collections[index_name]
            
            logger.info(f"成功删除索引: {index_name}")
            return True
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"删除索引失败: {str(e)}")
            raise IndexOperationError(f"delete操作失败: {str(e)}", operation="delete", index_name=index_name)

    def count_vectors(self, index_name: str) -> int:
        """
        统计索引中的向量数量
        
        Args:
            index_name: 索引名称
            
        Returns:
            int: 向量数量
            
        Raises:
            IndexNotFoundError: 当索引不存在时
        """
        try:
            # 获取集合
            collection = self._get_collection(index_name)
            
            # 获取所有ID并统计数量
            all_ids = collection.get()['ids']
            return len(all_ids)
            
        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"统计向量数量失败: {str(e)}")
            raise VectorOperationError("count", str(e))

    def close(self) -> None:
        """
        关闭连接，释放资源
        """
        try:
            # Chroma客户端目前没有显式的close方法
            # 清理集合缓存
            self.collections.clear()
            logger.info("Chroma客户端资源已释放")
            
        except Exception as e:
            logger.error(f"关闭Chroma客户端失败: {str(e)}")

    async def search_vectors_async(
        self,
        query_embedding: List[float],
        content_type: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        异步搜索向量（包装同步方法）
        
        Args:
            query_embedding: 查询向量
            content_type: 内容类型（实体或关系）
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        try:
            logger.debug(f"异步搜索向量开始: content_type='{content_type}', top_k={top_k}")
            
            # 构建过滤条件 - 使用ChromaDB支持的格式
            filter_dict = None
            if content_type:
                filter_dict = {"content_type": {"$eq": content_type}}
            logger.debug(f"构建过滤条件: {filter_dict}")
            
            # 调用同步搜索方法
            logger.debug(f"调用同步搜索方法: index_name='{content_type}', query_vector维度={len(query_embedding)}")
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                self.search_vectors,
                content_type,  # index_name
                query_embedding,
                top_k,
                filter_dict
            )
            
            logger.debug(f"异步搜索向量完成: 返回结果数量={len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"异步搜索向量失败: {str(e)}")
            raise VectorOperationError("search_async", str(e))

    def search_vectors_sync(
        self,
        query_embedding: List[float],
        content_type: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        同步搜索向量
        
        Args:
            query_embedding: 查询向量
            content_type: 内容类型（实体或关系）
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        try:
            # 构建过滤条件 - 使用ChromaDB支持的格式
            filter_dict = None
            if content_type:
                filter_dict = {"content_type": {"$eq": content_type}}
            
            # 调用同步搜索方法
            results = self.search_vectors(
                index_name=content_type,
                query_vector=query_embedding,
                top_k=top_k,
                filter_dict=filter_dict
            )
            
            return results
            
        except Exception as e:
            logger.error(f"同步搜索向量失败: {str(e)}")
            raise VectorOperationError("search_sync", str(e))

    async def update_vector_async(
        self,
        vector_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        异步更新向量（包装同步方法）
        
        Args:
            vector_id: 向量ID
            embedding: 新的向量
            metadata: 元数据
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 从metadata中获取内容类型
            content_type = metadata.get("content_type", "entity")
            
            # 调用同步更新方法
            success = await asyncio.get_event_loop().run_in_executor(
                None,
                self.update_vectors,
                content_type,  # index_name
                [embedding],
                [vector_id],
                [metadata]
            )
            
            return success
            
        except Exception as e:
            logger.error(f"异步更新向量失败: {str(e)}")
            raise VectorOperationError("update_async", str(e))

    def update_vector_sync(
        self,
        vector_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        同步更新向量
        
        Args:
            vector_id: 向量ID
            embedding: 新的向量
            metadata: 元数据
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 从metadata中获取内容类型
            content_type = metadata.get("content_type", "entity")
            
            # 调用同步更新方法
            success = self.update_vectors(
                index_name=content_type,
                vectors=[embedding],
                ids=[vector_id],
                metadatas=[metadata]
            )
            
            return success
            
        except Exception as e:
            logger.error(f"同步更新向量失败: {str(e)}")
            raise VectorOperationError("update_sync", str(e))

    async def delete_vector_async(self, vector_id: str) -> bool:
        """
        异步删除向量（包装同步方法）
        
        Args:
            vector_id: 向量ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 从向量ID中提取内容类型（假设格式为 content_type_uuid）
            content_type = vector_id.split("_")[0] if "_" in vector_id else "entity"
            
            # 调用同步删除方法
            success = await asyncio.get_event_loop().run_in_executor(
                None,
                self.delete_vectors,
                content_type,  # index_name
                [vector_id]
            )
            
            return success
            
        except Exception as e:
            logger.error(f"异步删除向量失败: {str(e)}")
            raise VectorOperationError("delete_async", str(e))

    def delete_vector_sync(self, vector_id: str) -> bool:
        """
        同步删除向量
        
        Args:
            vector_id: 向量ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 从向量ID中提取内容类型（假设格式为 content_type_uuid）
            content_type = vector_id.split("_")[0] if "_" in vector_id else "entity"
            
            # 调用同步删除方法
            success = self.delete_vectors(
                index_name=content_type,
                ids=[vector_id]
            )
            
            return success
            
        except Exception as e:
            logger.error(f"同步删除向量失败: {str(e)}")
            raise VectorOperationError("delete_sync", str(e))

    def health_check(self) -> str:
        """
        健康检查
        
        Returns:
            str: 健康状态（"healthy" 或 "unhealthy"）
        """
        try:
            # 尝试列出集合来检查连接
            collections = self.client.list_collections()
            return "healthy"
        except Exception as e:
            logger.error(f"Chroma健康检查失败: {str(e)}")
            return "unhealthy"
