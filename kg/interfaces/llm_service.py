"""
LLM服务接口模块

定义语言模型服务的标准接口，确保所有实现提供一致的功能
"""
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from .base_service import AsyncService


class LLMServiceInterface(AsyncService):
    """
    LLM服务接口
    
    定义与语言模型交互的标准方法
    """
    
    @abstractmethod
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取实体
        
        Args:
            text: 要分析的文本
            
        Returns:
            List[Dict[str, Any]]: 提取的实体列表
            
        Raises:
            ValueError: 当输入文本无效时
            RuntimeError: 当提取失败时
        """
        pass
    
    @abstractmethod
    async def extract_relations(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从文本中提取实体关系
        
        Args:
            text: 要分析的文本
            entities: 已提取的实体列表
            
        Returns:
            List[Dict[str, Any]]: 提取的关系列表
            
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当提取失败时
        """
        pass
    
    @abstractmethod
    async def summarize_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        总结文本内容
        
        Args:
            text: 要总结的文本
            max_length: 总结最大长度
            
        Returns:
            str: 文本摘要
            
        Raises:
            ValueError: 当输入文本无效时
            RuntimeError: 当总结失败时
        """
        pass
    
    @abstractmethod
    async def aggregate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        聚合相似实体
        
        Args:
            entities: 实体列表
            
        Returns:
            List[Dict[str, Any]]: 聚合后的实体列表
            
        Raises:
            ValueError: 当输入实体无效时
            RuntimeError: 当聚合失败时
        """
        pass
    
    @abstractmethod
    async def aggregate_relations(self, relations: List[Dict[str, Any]], entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        聚合相似关系
        
        Args:
            relations: 关系列表
            entities: 实体列表
            
        Returns:
            List[Dict[str, Any]]: 聚合后的关系列表
            
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当聚合失败时
        """
        pass
    
    @abstractmethod
    async def process_news_text(self, text: str) -> Dict[str, Any]:
        """
        处理新闻文本，执行完整分析流程
        
        Args:
            text: 新闻文本
            
        Returns:
            Dict[str, Any]: 包含实体、关系和摘要的完整分析结果
            
        Raises:
            ValueError: 当输入文本无效时
            RuntimeError: 当处理失败时
        """
        pass
