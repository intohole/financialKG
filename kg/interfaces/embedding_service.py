"""
Embedding服务接口模块

定义embedding服务的标准接口，确保所有实现提供一致的功能
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .base_service import AsyncService


class EmbeddingServiceInterface(AsyncService):
    """
    Embedding服务接口

    定义将文本转换为向量表示的标准方法
    """

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        将文本列表转换为embedding向量列表

        Args:
            texts: 要转换的文本列表

        Returns:
            List[List[float]]: 对应的embedding向量列表

        Raises:
            ValueError: 当输入文本无效时
            RuntimeError: 当获取embedding失败时
        """
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        将单个文本转换为embedding向量

        Args:
            text: 要转换的文本

        Returns:
            List[float]: 对应的embedding向量

        Raises:
            ValueError: 当输入文本无效时
            RuntimeError: 当获取embedding失败时
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        获取embedding向量的维度

        Returns:
            int: embedding向量的维度
        """
        pass

    @abstractmethod
    def is_valid_embedding(self, embedding: List[float]) -> bool:
        """
        验证embedding向量是否有效

        Args:
            embedding: 要验证的embedding向量

        Returns:
            bool: 向量是否有效
        """
        pass
