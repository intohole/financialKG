"""
服务层接口模块

提供高级业务逻辑，封装数据仓库操作，实现实体和关系的去重功能
"""
import logging
import json
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from kg.database.models import Entity, Relation, News, EntityNews, EntityGroup, RelationGroup
from kg.database.repositories import (
    EntityRepository, RelationRepository, NewsRepository, 
    EntityNewsRepository, EntityGroupRepository, RelationGroupRepository
)
from kg.database.connection import get_db_session, db_session
from kg.utils.db_utils import handle_db_errors, handle_db_errors_with_reraise, jsonify_properties

# 从新的数据库服务模块导入类
from .database.entity_service import EntityService
from .database.relation_service import RelationService
from .database.news_service import NewsService
from .database.knowledge_graph_service import KnowledgeGraphService

# 配置日志
logger = logging.getLogger(__name__)


# 保持向后兼容性，重新导出类
__all__ = [
    'EntityService',
    'RelationService',
    'NewsService',
    'KnowledgeGraphService'
]
