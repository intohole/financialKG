"""
存储层抽象基类
定义统一的数据存储接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StoreConfig:
    """存储配置"""
    vector_store_config: Dict[str, Any]
    metadata_store_config: Dict[str, Any]
    enable_vector_index: bool = True
    enable_full_text_search: bool = True
    sync_mode: str = "async"  # async, sync, eventual


@dataclass
class Entity:
    """实体数据模型"""
    name: str
    type: str
    description: Optional[str] = None
    id: Optional[int] = None
    canonical_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    vector_id: Optional[str] = None  # 对应的向量ID
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Relation:
    """关系数据模型"""
    id: Optional[int]
    subject_id: int
    predicate: str
    object_id: int
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    vector_id: Optional[str] = None  # 对应的向量ID
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class NewsEvent:
    """新闻事件数据模型"""
    id: Optional[int]
    title: str
    content: Optional[str]
    source: Optional[str] = None
    publish_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    vector_id: Optional[str] = None  # 对应的向量ID
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """搜索结果"""
    entity: Optional[Entity] = None
    relation: Optional[Relation] = None
    news_event: Optional[NewsEvent] = None
    score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class StoreBase(ABC):
    """存储层抽象基类"""

    @abstractmethod
    async def initialize(self, config: StoreConfig) -> None:
        """初始化存储层"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭存储连接"""
        pass

    # 实体操作
    @abstractmethod
    async def create_entity(self, entity: Entity) -> Entity:
        """创建实体"""
        pass

    @abstractmethod
    async def get_entity(self, entity_id: int) -> Optional[Entity]:
        """获取实体"""
        pass

    @abstractmethod
    async def update_entity(self, entity_id: int, updates: Dict[str, Any]) -> Entity:
        """更新实体"""
        pass

    @abstractmethod
    async def delete_entity(self, entity_id: int) -> bool:
        """删除实体"""
        pass

    @abstractmethod
    async def search_entities(self, 
                            query: str, 
                            entity_type: Optional[str] = None,
                            top_k: int = 10,
                            include_vector_search: bool = True,
                            include_full_text_search: bool = True) -> List[SearchResult]:
        """搜索实体"""
        pass

    # 关系操作
    @abstractmethod
    async def create_relation(self, relation: Relation) -> Relation:
        """创建关系"""
        pass

    @abstractmethod
    async def get_relation(self, relation_id: int) -> Optional[Relation]:
        """获取关系"""
        pass

    @abstractmethod
    async def get_entity_relations(self, entity_id: int, 
                                 predicate: Optional[str] = None) -> List[Relation]:
        """获取实体的所有关系"""
        pass

    @abstractmethod
    async def delete_relation(self, relation_id: int) -> bool:
        """删除关系"""
        pass

    # 新闻事件操作
    @abstractmethod
    async def create_news_event(self, news_event: NewsEvent) -> NewsEvent:
        """创建新闻事件"""
        pass

    @abstractmethod
    async def get_news_event(self, news_event_id: int) -> Optional[NewsEvent]:
        """获取新闻事件"""
        pass

    @abstractmethod
    async def search_news_events(self, 
                               query: str,
                               top_k: int = 10,
                               time_range: Optional[tuple] = None) -> List[SearchResult]:
        """搜索新闻事件"""
        pass

    # 向量操作
    @abstractmethod
    async def add_to_vector_index(self, 
                                content: str,
                                content_id: str,
                                content_type: str,
                                metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加到向量索引"""
        pass

    @abstractmethod
    async def search_vectors(self, 
                           query: str,
                           content_type: Optional[str] = None,
                           top_k: int = 10,
                           filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """向量搜索"""
        pass

    # 事务操作
    @abstractmethod
    async def begin_transaction(self) -> None:
        """开始事务"""
        pass

    @abstractmethod
    async def commit_transaction(self) -> None:
        """提交事务"""
        pass

    @abstractmethod
    async def rollback_transaction(self) -> None:
        """回滚事务"""
        pass

    # 健康检查
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        pass

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()