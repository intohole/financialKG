"""
Chroma向量数据库服务模块
提供向量存储和相似度查询功能
"""
import os
import logging
from typing import List, Dict, Any, Optional
from chromadb.api.async_client import AsyncClient
from chromadb.config import Settings

from kg.interfaces.vector_db_service import VectorDBServiceInterface
from kg.interfaces.base_service import AsyncService
from kg.utils import handle_errors

logger = logging.getLogger(__name__)

class ChromaService(VectorDBServiceInterface, AsyncService):
    """
    Chroma向量数据库服务实现
    继承自VectorDBServiceInterface和AsyncService
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Chroma向量数据库服务
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.chroma_client = None
        self.collections = {}  # 缓存已创建的集合
        
        # 配置参数
        self.persist_directory = self.config.get("PERSIST_DIRECTORY") or os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        self.embedding_function = self.config.get("EMBEDDING_FUNCTION")
    
    async def _init_client(self):
        """
        异步初始化Chroma客户端
        """
        if self.chroma_client is None:
            try:
                self.chroma_client = AsyncClient(
                    settings=Settings(
                        persist_directory=self.persist_directory,
                        chroma_db_impl="duckdb+parquet",
                        anonymized_telemetry=False
                    )
                )
                logger.info(f"Chroma客户端已初始化，持久化目录: {self.persist_directory}")
            except Exception as e:
                logger.error(f"初始化Chroma客户端失败: {str(e)}")
                raise
    
    @handle_errors(log_error=True, log_message="获取或创建Chroma集合失败: {error}")
    async def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """
        获取或创建集合
        
        Args:
            name: 集合名称
            metadata: 集合元数据
            
        Returns:
            集合对象
        """
        if name in self.collections:
            return self.collections[name]
        
        # 懒加载客户端
        await self._init_client()
        
        # 获取或创建集合
        collection = await self.chroma_client.get_or_create_collection(
            name=name,
            metadata=metadata or {},
            embedding_function=self.embedding_function
        )
        
        self.collections[name] = collection
        logger.info(f"已获取或创建Chroma集合: {name}")
        return collection
    
    @handle_errors(log_error=True, log_message="向集合添加embedding失败: {error}")
    async def add_embeddings(self, collection_name: str, documents: List[str], 
                            embeddings: List[List[float]], ids: List[str], 
                            metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        向集合中添加embedding向量
        
        Args:
            collection_name: 集合名称
            documents: 文档列表
            embeddings: embedding向量列表
            ids: 文档ID列表
            metadata: 文档元数据列表
            
        Returns:
            是否成功添加
        """
        if not documents or not embeddings or not ids:
            logger.warning("没有文档、embedding或ID可添加")
            return False
        
        if len(documents) != len(embeddings) or len(documents) != len(ids):
            logger.error("文档、embedding和ID的数量必须一致")
            return False
        
        collection = await self.get_or_create_collection(collection_name)
        
        await collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadata or []
        )
        
        logger.info(f"成功向集合 {collection_name} 添加了 {len(documents)} 个文档的embedding")
        return True
    
    @handle_errors(log_error=True, log_message="查询相似embedding失败: {error}")
    async def query_similar_embeddings(self, collection_name: str, 
                                      query_embeddings: List[List[float]], 
                                      n_results: int = 5, 
                                      where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        查询相似的embedding向量
        
        Args:
            collection_name: 集合名称
            query_embeddings: 查询embedding向量列表
            n_results: 返回结果数量
            where: 元数据过滤条件
            
        Returns:
            相似度查询结果
        """
        if not query_embeddings:
            logger.warning("没有查询embedding")
            return {}
        
        collection = await self.get_or_create_collection(collection_name)
        
        results = await collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )
        
        logger.info(f"成功查询到 {len(results.get('ids', []))} 组相似结果")
        return results
    
    @handle_errors(log_error=True, log_message="根据ID获取embedding失败: {error}")
    async def get_embeddings(self, collection_name: str, ids: List[str]) -> Dict[str, Any]:
        """
        根据ID获取embedding向量
        
        Args:
            collection_name: 集合名称
            ids: 文档ID列表
            
        Returns:
            embedding向量查询结果
        """
        if not ids:
            logger.warning("没有ID可查询")
            return {}
        
        collection = await self.get_or_create_collection(collection_name)
        
        results = await collection.get(ids=ids)
        
        logger.info(f"成功获取到 {len(results.get('ids', []))} 个embedding向量")
        return results
    
    @handle_errors(log_error=True, log_message="删除embedding失败: {error}")
    async def delete_embeddings(self, collection_name: str, ids: List[str]) -> bool:
        """
        根据ID删除embedding向量
        
        Args:
            collection_name: 集合名称
            ids: 文档ID列表
            
        Returns:
            是否成功删除
        """
        if not ids:
            logger.warning("没有ID可删除")
            return False
        
        collection = await self.get_or_create_collection(collection_name)
        
        await collection.delete(ids=ids)
        
        logger.info(f"成功删除了 {len(ids)} 个embedding向量")
        return True
    
    @handle_errors(log_error=True, log_message="更新embedding失败: {error}")
    async def update_embeddings(self, collection_name: str, 
                               ids: List[str], 
                               documents: Optional[List[str]] = None,
                               embeddings: Optional[List[List[float]]] = None,
                               metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        更新embedding向量
        
        Args:
            collection_name: 集合名称
            ids: 文档ID列表
            documents: 文档列表
            embeddings: embedding向量列表
            metadata: 文档元数据列表
            
        Returns:
            是否成功更新
        """
        if not ids:
            logger.warning("没有ID可更新")
            return False
        
        collection = await self.get_or_create_collection(collection_name)
        
        update_dict = {"ids": ids}
        if documents:
            update_dict["documents"] = documents
        if embeddings:
            update_dict["embeddings"] = embeddings
        if metadata:
            update_dict["metadatas"] = metadata
        
        await collection.update(**update_dict)
        
        logger.info(f"成功更新了 {len(ids)} 个embedding向量")
        return True

@handle_errors(log_error=True, log_message="创建Chroma服务实例失败: {error}")
def create_chroma_service(config: Optional[Dict[str, Any]] = None) -> ChromaService:
    """
    创建Chroma服务实例
    
    Args:
        config: 配置参数
        
    Returns:
        ChromaService实例
    """
    return ChromaService(config)

# 注册服务
from kg.utils.service_utils import register_service
register_service('vector_db', create_chroma_service)
