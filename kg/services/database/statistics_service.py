import logging
from typing import Any, Dict

from kg.services.database.entity_service import EntityService
from kg.services.database.news_service import NewsService
from kg.services.database.relation_service import RelationService
from kg.utils.db_utils import handle_db_errors

logger = logging.getLogger(__name__)


class StatisticsService:
    """
    知识图谱统计信息服务
    负责处理知识图谱的各种统计信息
    """

    def __init__(
        self,
        entity_service: EntityService,
        relation_service: RelationService,
        news_service: NewsService,
    ):
        self.entity_service = entity_service
        self.relation_service = relation_service
        self.news_service = news_service

    @handle_db_errors(default_return={})
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取知识图谱统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        logger.info("开始获取知识图谱统计信息")

        # 获取实体统计
        entities = await self.entity_service.entity_repo.get_all()
        entity_count = len(entities)

        # 统计实体类型
        entity_type_counts = {}
        for entity in entities:
            if entity.type not in entity_type_counts:
                entity_type_counts[entity.type] = 0
            entity_type_counts[entity.type] += 1

        # 获取关系统计
        relations = await self.relation_service.relation_repo.get_all()
        relation_count = len(relations)

        # 统计关系类型
        relation_type_counts = {}
        for relation in relations:
            if relation.relation_type not in relation_type_counts:
                relation_type_counts[relation.relation_type] = 0
            relation_type_counts[relation.relation_type] += 1

        # 获取新闻统计
        news = await self.news_service.news_repo.get_all()
        news_count = len(news)

        # 统计新闻状态
        news_status_counts = {}
        for news_item in news:
            if news_item.extraction_status not in news_status_counts:
                news_status_counts[news_item.extraction_status] = 0
            news_status_counts[news_item.extraction_status] += 1

        # 获取实体组统计
        entity_groups = await self.entity_service.entity_group_repo.get_all()
        entity_group_count = len(entity_groups)

        # 获取关系组统计
        relation_groups = await self.relation_service.relation_group_repo.get_all()
        relation_group_count = len(relation_groups)

        statistics = {
            "entities": {"total": entity_count, "by_type": entity_type_counts},
            "relations": {"total": relation_count, "by_type": relation_type_counts},
            "news": {"total": news_count, "by_status": news_status_counts},
            "entity_groups": entity_group_count,
            "relation_groups": relation_group_count,
        }
        logger.info(f"完成获取知识图谱统计信息: {statistics}")
        return statistics
