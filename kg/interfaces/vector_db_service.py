"""
向量数据库服务接口模块

定义向量数据库操作的标准接口，确保所有实现提供一致的功能
"""
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from .base_service import AsyncService


class VectorDBServiceInterface(AsyncService):
    """
    向量数据库服务接口
    
    定义向量存储和相似度查询的标准方法
    """
    
    @abstractmethod
    async def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """
        获取或创建向量集合
        
        Args:
            name: 集合名称
            metadata: 集合元数据
            
        Returns:
            集合对象
            
        Raises:
            RuntimeError: 当操作失败时
        """
        pass
    
    @abstractmethod
    async def add_embeddings(self, collection_name: str, 
                           documents: List[str], 
                           embeddings: List[List[float]], 
                           ids: List[str], 
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
            bool: 是否成功添加
            
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当添加失败时
        """
        pass
    
    @abstractmethod
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
            Dict[str, Any]: 相似度查询结果
            
        Raises:
            ValueError: 当查询参数无效时
            RuntimeError: 当查询失败时
        """
        pass
    
    @abstractmethod
    async def get_embeddings(self, collection_name: str, ids: List[str]) -> Dict[str, Any]:
        """
        根据ID获取embedding向量
        
        Args:
            collection_name: 集合名称
            ids: 文档ID列表
            
        Returns:
            Dict[str, Any]: embedding向量查询结果
            
        Raises:
            ValueError: 当ID列表无效时
            RuntimeError: 当查询失败时
        """
        pass
    
    @abstractmethod
    async def delete_embeddings(self, collection_name: str, ids: List[str]) -> bool:
        """
        根据ID删除embedding向量
        
        Args:
            collection_name: 集合名称
            ids: 文档ID列表
            
        Returns:
            bool: 是否成功删除
            
        Raises:
            ValueError: 当ID列表无效时
            RuntimeError: 当删除失败时
        """
        pass
    
    @abstractmethod
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
            bool: 是否成功更新
            
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当更新失败时
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        关闭向量数据库连接
        """
        pass
