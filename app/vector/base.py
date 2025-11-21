"""
向量搜索接口抽象基类
定义向量数据库操作的核心功能接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union


class VectorSearchBase(ABC):
    """
    向量搜索接口抽象基类
    定义向量数据库操作的标准接口
    """

    @abstractmethod
    def create_index(self, index_name: str, dimension: int, **kwargs) -> bool:
        """
        创建向量索引
        
        Args:
            index_name: 索引名称
            dimension: 向量维度
            **kwargs: 其他索引配置参数
            
        Returns:
            bool: 创建是否成功
        """
        pass

    @abstractmethod
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
            texts: 原始文本列表（如果有）
            **kwargs: 其他参数
            
        Returns:
            bool: 添加是否成功
        """
        pass

    @abstractmethod
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
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表，每个结果包含id、向量、元数据、相似度分数等
        """
        pass

    @abstractmethod
    def delete_vectors(self, index_name: str, ids: List[str]) -> bool:
        """
        删除向量
        
        Args:
            index_name: 索引名称
            ids: 要删除的向量ID列表
            
        Returns:
            bool: 删除是否成功
        """
        pass

    @abstractmethod
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
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_index_info(self, index_name: str) -> Dict[str, Any]:
        """
        获取索引信息
        
        Args:
            index_name: 索引名称
            
        Returns:
            Dict[str, Any]: 索引信息
        """
        pass

    @abstractmethod
    def list_indices(self) -> List[str]:
        """
        列出所有索引
        
        Returns:
            List[str]: 索引名称列表
        """
        pass

    @abstractmethod
    def delete_index(self, index_name: str) -> bool:
        """
        删除索引
        
        Args:
            index_name: 索引名称
            
        Returns:
            bool: 删除是否成功
        """
        pass

    @abstractmethod
    def count_vectors(self, index_name: str) -> int:
        """
        统计索引中的向量数量
        
        Args:
            index_name: 索引名称
            
        Returns:
            int: 向量数量
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        关闭连接，释放资源
        """
        pass

    def __enter__(self):
        """
        上下文管理器入口
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        """
        self.close()
