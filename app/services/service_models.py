"""
服务层专用模型

为核心服务层提供必要的数据模型，这些模型专门用于服务层之间的数据传递。
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsContent:
    """新闻内容模型
    
    用于服务层之间传递新闻内容信息。
    
    属性：
        id (str): 内容唯一标识符
        title (str): 新闻标题
        content (str): 新闻内容
        url (Optional[str]): 原始URL
        publish_time (Optional[datetime]): 发布时间
        source (Optional[str]): 新闻来源
        author (Optional[str]): 作者
        category (Optional[str]): 分类
        tags (Optional[list]): 标签列表
        metadata (Optional[Dict[str, Any]]): 元数据
    """
    id: str
    title: str
    content: str
    url: Optional[str] = None
    publish_time: Optional[datetime] = None
    source: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "source": self.source,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata
        }


@dataclass
class SummaryResult:
    """摘要结果模型
    
    用于服务层之间传递摘要生成结果。
    
    属性：
        summary (str): 摘要文本
        keywords (list): 关键词列表
        importance_score (float): 重要性评分
        success (bool): 是否成功
        error (Optional[str]): 错误信息
        processing_time (float): 处理时间
    """
    summary: str
    keywords: list
    importance_score: float
    success: bool = True
    error: Optional[str] = None
    processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "summary": self.summary,
            "keywords": self.keywords,
            "importance_score": self.importance_score,
            "success": self.success,
            "error": self.error,
            "processing_time": self.processing_time
        }


@dataclass
class EntityExtraction:
    """实体提取结果模型"""
    entities: list
    success: bool = True
    error: Optional[str] = None
    processing_time: float = 0.0


@dataclass
class RelationExtraction:
    """关系提取结果模型"""
    relations: list
    success: bool = True
    error: Optional[str] = None
    processing_time: float = 0.0


@dataclass
class EntitySimilarity:
    """实体相似度模型"""
    entity1: Dict[str, Any]
    entity2: Dict[str, Any]
    similarity_score: float
    is_same_entity: bool
    reasoning: Optional[str] = None


@dataclass
class EntityDisambiguation:
    """实体消歧结果模型"""
    disambiguated_entities: list
    success: bool = True
    error: Optional[str] = None
    processing_time: float = 0.0