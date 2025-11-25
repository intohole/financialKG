"""
核心模块初始化文件
"""
from app.core.content_processor import ContentProcessor
from app.core.entity_analyzer import EntityAnalyzer
from app.core.content_summarizer import ContentSummarizer
from app.core.models import (
    ContentClassificationResult,
    ContentSummary,
    Entity,
    EntityResolutionResult,
    EntityComparisonResult,
    SimilarEntityResult,
    KnowledgeExtractionResult,
    Relation
)

__all__ = [
    # 核心服务类
    'ContentProcessor',
    'EntityAnalyzer', 
    'ContentSummarizer',
    
    # 数据模型
    'ContentClassificationResult',
    'ContentSummary',
    'Entity',
    'EntityResolutionResult',
    'EntityComparisonResult',
    'SimilarEntityResult',
    'KnowledgeExtractionResult',
    'Relation'
]