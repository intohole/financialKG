"""知识图谱核心模型

定义知识图谱相关的数据模型和结构，提供统一的数据表示和转换接口。

该模块包含了项目中使用的所有核心数据模型，包括实体、关系、知识图谱、
内容分类、实体相似度等，支持数据序列化和反序列化操作。

主要功能：
- 实体和关系模型的定义与管理
- 内容分类和知识提取结果模型
- 实体消歧和相似度计算结果模型
- 内容摘要和关键词提取结果模型
- 统一的数据字典转换接口

使用示例：
    >>> entity = Entity(name="苹果公司", type="公司", description="科技公司")
    >>> relation = Relation(subject="苹果公司", predicate="生产", object="iPhone")
    >>> result = ContentClassification(is_financial_content=True, confidence=0.95)
"""

from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ContentCategory(str, Enum):
    """内容类别枚举"""
    FINANCIAL = "financial"
    TECHNOLOGY = "technology"
    MEDICAL = "medical"
    EDUCATION = "education"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """实体模型
    
    表示知识图谱中的实体，包含实体的基本信息和元数据。
    
    属性：
        name (str): 实体名称，必填字段
        type (str): 实体类型，必填字段
        description (Optional[str]): 实体描述，可选
        id (Optional[int]): 实体ID，数据库主键
        canonical_id (Optional[int]): 标准实体ID，用于实体消歧
        created_at (Optional[datetime]): 创建时间
        updated_at (Optional[datetime]): 更新时间
        category (Optional[str]): 实体类别
    
    使用示例：
        >>> entity = Entity(
        ...     name="苹果公司",
        ...     type="公司",
        ...     description="全球领先的科技公司",
        ...     category="科技企业"
        ... )
        >>> entity_dict = entity.to_dict()
    """
    name: str
    type: str
    description: Optional[str] = None
    id: Optional[int] = None
    canonical_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """将实体转换为字典"""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "id": self.id,
            "canonical_id": self.canonical_id,
            "category": self.category,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class Relation:
    """关系模型
    
    表示知识图谱中的实体关系，支持传统三元组和新的实体关系表示方式。
    
    属性：
        subject (str): 关系主体，必填字段
        predicate (str): 关系谓词，必填字段
        object (str): 关系客体，必填字段
        description (Optional[str]): 关系描述
        id (Optional[int]): 关系ID，数据库主键
        subject_id (Optional[int]): 主体实体ID
        object_id (Optional[int]): 客体实体ID
        created_at (Optional[datetime]): 创建时间
        category (Optional[str]): 关系类别
        source_entity (Optional[str]): 源实体名称（新字段）
        target_entity (Optional[str]): 目标实体名称（新字段）
        relation_type (Optional[str]): 关系类型（新字段）
        confidence (Optional[float]): 关系置信度，范围0-1
        properties (Optional[Dict[str, Any]]): 关系属性字典
    
    使用示例：
        >>> relation = Relation(
        ...     subject="苹果公司",
        ...     predicate="生产",
        ...     object="iPhone",
        ...     confidence=0.95,
        ...     description="苹果公司生产iPhone手机"
        ... )
        >>> relation_dict = relation.to_dict()
    """
    subject: str
    predicate: str
    object: str
    description: Optional[str] = None
    id: Optional[int] = None
    subject_id: Optional[int] = None
    object_id: Optional[int] = None
    created_at: Optional[datetime] = None
    category: Optional[str] = None
    # 新增字段，兼容新的实体关系提取
    source_entity: Optional[str] = None
    target_entity: Optional[str] = None
    relation_type: Optional[str] = None
    confidence: Optional[float] = None
    properties: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """后初始化处理"""
        # 如果使用了新的字段名，自动同步到传统字段
        if self.source_entity and not self.subject:
            self.subject = self.source_entity
        if self.target_entity and not self.object:
            self.object = self.target_entity
        if self.relation_type and not self.predicate:
            self.predicate = self.relation_type
    
    def to_dict(self) -> Dict[str, Any]:
        """将关系转换为字典"""
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "description": self.description,
            "id": self.id,
            "subject_id": self.subject_id,
            "object_id": self.object_id,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            # 新增字段
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "properties": self.properties
        }


@dataclass
class KnowledgeGraph:
    """知识图谱模型"""
    entities: List[Entity]
    relations: List[Relation]
    metadata: Optional[Dict[str, Any]] = None
    category: Optional[str] = None


@dataclass
class ContentClassification:
    """内容分类结果
    
    表示内容分类的结果，包含分类信息、置信度和推理过程。
    
    属性：
        is_financial_content (bool): 是否为金融内容
        confidence (float): 分类置信度，范围0-1
        category (Optional[str]): 内容类别
        reasoning (Optional[str]): 分类推理过程
        supported_categories (List[str]): 支持的类别列表
    
    使用示例：
        >>> classification = ContentClassification(
        ...     is_financial_content=True,
        ...     confidence=0.95,
        ...     category="financial",
        ...     reasoning="文本包含股票、投资等金融关键词"
        ... )
        >>> is_supported = classification.is_category_supported("financial")
    """
    is_financial_content: bool
    confidence: float
    category: Optional[str] = None
    reasoning: Optional[str] = None
    supported_categories: List[str] = None

    def __post_init__(self):
        if self.supported_categories is None:
            self.supported_categories = []

    def is_category_supported(self, category: str) -> bool:
        """检查类别是否受支持"""
        return category in self.supported_categories
    
    def to_dict(self) -> Dict[str, Any]:
        """将内容分类结果转换为字典"""
        return {
            "is_financial_content": self.is_financial_content,
            "confidence": self.confidence,
            "category": self.category,
            "reasoning": self.reasoning,
            "supported_categories": self.supported_categories
        }


@dataclass
class ContentClassificationResult:
    """内容分类结果（新版本）"""
    category: ContentCategory
    confidence: float
    reasoning: Optional[str] = None
    is_financial_content: bool = False
    supported: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """将内容分类结果转换为字典"""
        return {
            "category": self.category.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "is_financial_content": self.is_financial_content,
            "supported": self.supported
        }


@dataclass
class CategoryConfig:
    """类别配置模型"""
    name: str
    description: str
    entity_types: List[str]
    relation_types: List[str]

    def supports_entity_type(self, entity_type: str) -> bool:
        """检查是否支持实体类型"""
        return entity_type in self.entity_types

    def supports_relation_type(self, relation_type: str) -> bool:
        """检查是否支持关系类型"""
        return relation_type in self.relation_types


@dataclass
class EntitySimilarity:
    """实体相似度模型"""
    entity1: Entity
    entity2: Entity
    similarity_score: float
    is_same_entity: bool
    reasoning: Optional[str] = None


@dataclass
class KnowledgeExtractionResult:
    """知识提取结果"""
    content_classification: ContentClassification
    knowledge_graph: KnowledgeGraph
    raw_text: str
    processing_time: Optional[float] = None


@dataclass
class EntityResolutionResult:
    """实体消歧结果"""
    selected_entity: Optional[Entity]
    confidence: float
    reasoning: Optional[str] = None


@dataclass
class EntityComparisonResult:
    """实体比较结果"""
    entity1: Entity
    entity2: Entity
    similarity_score: float
    is_same_entity: bool
    reasoning: Optional[str] = None


@dataclass
class SimilarEntityResult:
    """相似实体结果"""
    entity: Entity
    similarity_score: float
    reasoning: Optional[str] = None


@dataclass
class ContentSummary:
    """内容摘要结果
    
    表示内容摘要的结果，包含摘要文本、关键词、重要性评分等信息。
    
    属性：
        summary (str): 摘要文本内容
        keywords (List[str]): 关键词列表
        importance_score (int): 重要性评分，范围1-10
        original_length (int): 原文长度，默认为0
        summary_length (int): 摘要长度，默认为0
        compression_ratio (float): 压缩比例，默认为0.0
        importance_reason (str): 重要性评分理由，默认为空字符串
        success (bool): 是否成功生成摘要，默认为True
        error (Optional[str]): 错误信息，失败时提供
    
    使用示例：
        >>> summary = ContentSummary(
        ...     summary="苹果公司发布了新款iPhone，市场反应积极",
        ...     keywords=["苹果", "iPhone", "发布", "市场"],
        ...     importance_score=8,
        ...     importance_reason="涉及重要产品发布信息"
        ... )
        >>> summary_dict = summary.to_dict()
    """
    summary: str
    keywords: List[str]
    importance_score: int
    original_length: int = 0
    summary_length: int = 0
    compression_ratio: float = 0.0
    importance_reason: str = ""
    success: bool = True
    error: Optional[str] = None