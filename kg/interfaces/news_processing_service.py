"""
新闻处理服务接口模块

定义新闻处理的标准接口，确保所有实现提供一致的功能
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .base_service import AsyncService


class NewsProcessingServiceInterface(AsyncService):
    """
    新闻处理服务接口

    定义新闻内容处理和存储的标准方法
    """

    @abstractmethod
    async def process_and_store_news(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理并存储新闻数据

        Args:
            news_data: 包含新闻内容的字典，必须包含title和content字段

        Returns:
            Dict[str, Any]: 处理结果，包含原始数据和处理后的实体、关系、摘要等

        Raises:
            ValueError: 当输入新闻数据无效时
            RuntimeError: 当处理或存储失败时
        """
        pass

    @abstractmethod
    async def validate_news_data(self, news_data: Dict[str, Any]) -> bool:
        """
        验证新闻数据格式

        Args:
            news_data: 要验证的新闻数据

        Returns:
            bool: 数据是否有效

        Raises:
            ValueError: 当数据格式严重错误时
        """
        pass

    @abstractmethod
    async def get_processing_status(self, news_id: str) -> Dict[str, Any]:
        """
        获取新闻处理状态

        Args:
            news_id: 新闻ID

        Returns:
            Dict[str, Any]: 处理状态信息

        Raises:
            ValueError: 当新闻ID无效时
            RuntimeError: 当查询失败时
        """
        pass

    @abstractmethod
    async def batch_process_news(
        self, news_list: list[Dict[str, Any]], batch_size: int = 10
    ) -> list[Dict[str, Any]]:
        """
        批量处理新闻列表

        Args:
            news_list: 新闻数据列表
            batch_size: 批次大小

        Returns:
            list[Dict[str, Any]]: 处理结果列表

        Raises:
            ValueError: 当输入列表无效时
            RuntimeError: 当批量处理失败时
        """
        pass
