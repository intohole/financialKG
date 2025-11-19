"""
知识图谱数据库模块

提供知识图谱数据的存储、查询和管理功能，包括：
- 实体和关系的存储与去重
- 新闻数据的存储
- 数据库连接管理
- 数据访问接口
"""

from .connection import (db_session, get_db_manager, get_db_session,
                         init_database)
from .models import (Entity, EntityGroup, EntityNews, News, Relation,
                     RelationGroup)
from .repositories import (EntityGroupRepository, EntityRepository,
                           NewsRepository, RelationGroupRepository,
                           RelationRepository)

__all__ = [
    # 连接管理
    "get_db_manager",
    "get_db_session",
    "db_session",
    "init_database",
    # 数据模型
    "Entity",
    "Relation",
    "News",
    "EntityNews",
    "EntityGroup",
    "RelationGroup",
    # 仓库接口
    "EntityRepository",
    "RelationRepository",
    "NewsRepository",
    "EntityGroupRepository",
    "RelationGroupRepository",
]
