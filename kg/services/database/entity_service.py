import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from kg.database.connection import get_db_session
from kg.database.models import Entity, EntityGroup, EntityNews, News, Relation
from kg.database.repositories import (EntityGroupRepository,
                                      EntityNewsRepository, EntityRepository,
                                      NewsRepository, RelationRepository)
from kg.utils.db_utils import (handle_db_errors, handle_db_errors_with_reraise,
                               jsonify_properties)

# 配置日志
logger = logging.getLogger(__name__)


class EntityService:
    """实体服务类，提供实体相关的高级操作"""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.session = db
        self.entity_repo = EntityRepository(db)
        self.entity_group_repo = EntityGroupRepository(db)
        self.entity_news_repo = EntityNewsRepository(db)

    @handle_db_errors_with_reraise()
    async def create_entity(
        self,
        name: str,
        entity_type: str,
        canonical_name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        confidence_score: float = 0.0,
        source: Optional[str] = None,
    ) -> Entity:
        """
        创建实体

        Args:
            name: 实体名称
            entity_type: 实体类型
            canonical_name: 规范名称
            properties: 实体属性
            confidence_score: 置信度分数
            source: 实体来源

        Returns:
            Entity: 创建的实体对象
        """
        properties_json = jsonify_properties(properties)

        entity = await self.entity_repo.create(
            name=name,
            type=entity_type,
            canonical_name=canonical_name,
            properties=properties_json,
            confidence_score=confidence_score,
            source=source,
        )

        logger.info(f"创建实体成功: {name} (ID: {entity.id})")
        return entity

    @handle_db_errors_with_reraise()
    async def get_or_create_entity(
        self,
        name: str,
        entity_type: str,
        canonical_name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        confidence_score: float = 0.0,
        source: Optional[str] = None,
    ) -> Entity:
        """
        获取或创建实体

        Args:
            name: 实体名称
            entity_type: 实体类型
            canonical_name: 规范名称
            properties: 实体属性
            confidence_score: 置信度分数
            source: 实体来源

        Returns:
            Entity: 获取或创建的实体对象
        """
        entity = await self.entity_repo.get_or_create(
            name=name,
            entity_type=entity_type,
            canonical_name=canonical_name,
            properties=jsonify_properties(properties),
            source=source,
        )
        logger.debug(f"获取或创建实体: {name} (ID: {entity.id})")
        return entity

    @handle_db_errors(default_return=[])
    async def get_entities_by_names(self, names: List[str]) -> List[Entity]:
        """
        根据名称列表批量获取实体

        Args:
            names: 实体名称列表

        Returns:
            List[Entity]: 实体列表
        """
        return await self.entity_repo.get_by_names(names)

    @handle_db_errors(default_return=[])
    async def find_similar_entities(
        self, name: str, entity_type: str, threshold: float = 0.8
    ) -> List[Entity]:
        """
        查找相似实体

        Args:
            name: 实体名称
            entity_type: 实体类型
            threshold: 相似度阈值

        Returns:
            List[Entity]: 相似的实体列表
        """
        # 这里可以使用更复杂的相似度计算算法，如编辑距离、语义相似度等
        # 简单实现：查找名称包含关键词或类型相同的实体
        entities = await self.entity_repo.search_entities(name)

        # 过滤出相同类型的实体
        same_type_entities = [e for e in entities if e.type == entity_type]

        # 这里可以添加更精确的相似度计算
        # 返回相似度大于阈值的实体
        return same_type_entities

    @handle_db_errors_with_reraise()
    async def merge_entities(
        self,
        entity_ids: List[int],
        canonical_name: str,
        description: Optional[str] = None,
    ) -> EntityGroup:
        """
        合并实体，创建实体分组

        Args:
            entity_ids: 要合并的实体ID列表
            canonical_name: 合并后的规范名称
            description: 分组描述

        Returns:
            EntityGroup: 创建的实体分组对象
        """
        # 创建实体分组
        entity_group = await self.entity_group_repo.create(
            group_name=canonical_name, description=description
        )

        # 更新所有实体的分组ID和规范名称
        for entity_id in entity_ids:
            entity = await self.entity_repo.get(entity_id)
            if entity:
                await self.entity_repo.update(
                    entity_id,
                    entity_group_id=entity_group.id,
                    canonical_name=canonical_name,
                )

        # 设置主要实体ID（选择置信度最高的实体）
        entities = [
            await self.entity_repo.get(eid)
            for eid in entity_ids
            if await self.entity_repo.get(eid)
        ]
        if entities:
            primary_entity = max(entities, key=lambda e: e.confidence_score or 0)
            await self.entity_group_repo.update(
                entity_group.id, primary_entity_id=primary_entity.id
            )

        logger.info(f"合并实体成功: {canonical_name}, 包含 {len(entity_ids)} 个实体")
        return entity_group

    @handle_db_errors(default_return=None)
    async def get_entity_by_id(self, entity_id: int) -> Optional[Entity]:
        """根据ID获取实体"""
        return await self.entity_repo.get(entity_id)

    @handle_db_errors(default_return=[])
    async def get_entities_by_group(self, entity_group_id: int) -> List[Entity]:
        """根据分组ID获取实体"""
        return await self.entity_repo.find_by_group_id(entity_group_id)

    @handle_db_errors(default_return=[])
    async def get_entities_by_type(
        self, entity_type: str, limit: Optional[int] = None
    ) -> List[Entity]:
        """根据类型获取实体"""
        return await self.entity_repo.find_by_type(entity_type, limit)

    @handle_db_errors(default_return=[])
    async def get_all_entities(self, limit: Optional[int] = None) -> List[Entity]:
        """获取所有实体"""
        return await self.entity_repo.get_all(limit=limit)

    @handle_db_errors_with_reraise()
    async def search_entities(
        self,
        keyword: str,
        entity_type: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        sort_desc: bool = False,
    ) -> Tuple[List[Entity], int]:
        """
        搜索实体并支持分页、排序

        Args:
            keyword: 搜索关键词
            entity_type: 实体类型
            page: 页码
            limit: 每页大小
            order_by: 排序字段
            sort_desc: 是否降序排序

        Returns:
            Tuple[List[Entity], int]: 实体列表和总记录数
        """
        return await self.entity_repo.search_entities(keyword, entity_type, page, limit, order_by, sort_desc)

    @handle_db_errors(default_return=[])
    async def get_entity_news(
        self, entity_id: int, limit: Optional[int] = None
    ) -> List[News]:
        """获取实体相关的新闻"""
        return await self.entity_news_repo.get_news_by_entity(entity_id, limit)

    @handle_db_errors(default_return=None)
    async def update_entity(self, entity_id: int, **kwargs) -> Optional[Entity]:
        """更新实体"""
        if "properties" in kwargs and kwargs["properties"]:
            kwargs["properties"] = json.dumps(kwargs["properties"])
        return await self.entity_repo.update(entity_id, **kwargs)

    @handle_db_errors(default_return=None)
    async def delete_entity(self, entity_id: int) -> bool:
        """删除实体"""
        return await self.entity_repo.delete(entity_id)
