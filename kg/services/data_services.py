"""
服务层接口模块

主要用于统一导出各种服务类，提供简洁的导入接口
"""

# 从新的数据库服务模块导入类
from kg.services.database.entity_service import EntityService
from kg.services.database.knowledge_graph_service import KnowledgeGraphService
from kg.services.database.news_service import NewsService
from kg.services.database.relation_service import RelationService
from kg.services.entity_relation_deduplication_service import \
    EntityRelationDeduplicationService
from kg.services.integration import (DeduplicationServiceRegistry,
                                     create_deduplication_service_provider,
                                     register_deduplication_tasks)

# 保持向后兼容性，重新导出类
__all__ = [
    "EntityService",
    "RelationService",
    "NewsService",
    "KnowledgeGraphService",
    "EntityRelationDeduplicationService",
    "DeduplicationServiceRegistry",
    "create_deduplication_service_provider",
    "register_deduplication_tasks",
]
