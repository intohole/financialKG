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
from kg.utils.db_utils import handle_db_errors, handle_db_errors_with_reraise

# 配置日志
logger = logging.getLogger(__name__)


class EntityService:
    """实体服务类，提供实体相关的高级操作"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_db_session()
        self.entity_repo = EntityRepository(self.session)
        self.entity_group_repo = EntityGroupRepository(self.session)
        self.entity_news_repo = EntityNewsRepository(self.session)
    
    @handle_db_errors_with_reraise()
    def create_entity(self, name: str, entity_type: str, canonical_name: Optional[str] = None,
                     properties: Optional[Dict[str, Any]] = None, confidence_score: float = 0.0,
                     source: Optional[str] = None) -> Entity:
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
        properties_json = json.dumps(properties) if properties else None
        
        entity = self.entity_repo.create(
            name=name,
            type=entity_type,
            canonical_name=canonical_name,
            properties=properties_json,
            confidence_score=confidence_score,
            source=source
        )
        
        logger.info(f"创建实体成功: {name} (ID: {entity.id})")
        return entity
    
    @handle_db_errors_with_reraise()
    def get_or_create_entity(self, name: str, entity_type: str, canonical_name: Optional[str] = None,
                            properties: Optional[Dict[str, Any]] = None, confidence_score: float = 0.0,
                            source: Optional[str] = None) -> Entity:
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
        entity = self.entity_repo.get_or_create(
            name=name,
            entity_type=entity_type,
            canonical_name=canonical_name,
            properties=json.dumps(properties) if properties else None,
            source=source
        )
        logger.debug(f"获取或创建实体: {name} (ID: {entity.id})")
        return entity
    
    @handle_db_errors(default_return=[])
    def find_similar_entities(self, name: str, entity_type: str, threshold: float = 0.8) -> List[Entity]:
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
        entities = self.entity_repo.search_entities(name)
        
        # 过滤出相同类型的实体
        same_type_entities = [e for e in entities if e.type == entity_type]
        
        # 这里可以添加更精确的相似度计算
        # 返回相似度大于阈值的实体
        return same_type_entities
    
    @handle_db_errors_with_reraise()
    def merge_entities(self, entity_ids: List[int], canonical_name: str, 
                      description: Optional[str] = None) -> EntityGroup:
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
        entity_group = self.entity_group_repo.create(
            group_name=canonical_name,
            description=description
        )
        
        # 更新所有实体的分组ID和规范名称
        for entity_id in entity_ids:
            entity = self.entity_repo.get(entity_id)
            if entity:
                self.entity_repo.update(
                    entity_id,
                    entity_group_id=entity_group.id,
                    canonical_name=canonical_name
                )
        
        # 设置主要实体ID（选择置信度最高的实体）
        entities = [self.entity_repo.get(eid) for eid in entity_ids if self.entity_repo.get(eid)]
        if entities:
            primary_entity = max(entities, key=lambda e: e.confidence_score or 0)
            self.entity_group_repo.update(entity_group.id, primary_entity_id=primary_entity.id)
        
        logger.info(f"合并实体成功: {canonical_name}, 包含 {len(entity_ids)} 个实体")
        return entity_group
    
    @handle_db_errors(default_return=None)
    def get_entity_by_id(self, entity_id: int) -> Optional[Entity]:
        """根据ID获取实体"""
        return self.entity_repo.get(entity_id)
    
    @handle_db_errors(default_return=[])
    def get_entities_by_group(self, entity_group_id: int) -> List[Entity]:
        """根据分组ID获取实体"""
        return self.entity_repo.find_by_group_id(entity_group_id)
    
    @handle_db_errors(default_return=[])
    def get_entities_by_type(self, entity_type: str, limit: Optional[int] = None) -> List[Entity]:
        """根据类型获取实体"""
        return self.entity_repo.find_by_type(entity_type)
    
    @handle_db_errors(default_return=[])
    def search_entities(self, keyword: str, entity_type: Optional[str] = None, 
                       limit: Optional[int] = None) -> List[Entity]:
        """搜索实体"""
        return self.entity_repo.search_entities(keyword, limit)
    
    @handle_db_errors(default_return=[])
    def get_entity_news(self, entity_id: int, limit: Optional[int] = None) -> List[News]:
        """获取实体相关的新闻"""
        return self.entity_news_repo.get_news_by_entity(entity_id, limit)
    
    @handle_db_errors(default_return=None)
    def update_entity(self, entity_id: int, **kwargs) -> Optional[Entity]:
        """更新实体"""
        if 'properties' in kwargs and kwargs['properties']:
            kwargs['properties'] = json.dumps(kwargs['properties'])
        return self.entity_repo.update(entity_id, **kwargs)


class RelationService:
    """关系服务类，提供关系相关的高级操作"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_db_session()
        self.relation_repo = RelationRepository(self.session)
        self.relation_group_repo = RelationGroupRepository(self.session)
        self.entity_service = EntityService(self.session)
    
    @handle_db_errors_with_reraise()
    def create_relation(self, source_entity_id: int, target_entity_id: int, 
                       relation_type: str, canonical_relation: Optional[str] = None,
                       properties: Optional[Dict[str, Any]] = None, weight: float = 1.0,
                       source: Optional[str] = None) -> Relation:
        """
        创建关系
        
        Args:
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID
            relation_type: 关系类型
            canonical_relation: 规范关系类型
            properties: 关系属性
            weight: 关系权重
            source: 关系来源
            
        Returns:
            Relation: 创建的关系对象
        """
        relation = self.relation_repo.create(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relation_type=relation_type,
            canonical_relation=canonical_relation,
            properties=json.dumps(properties) if properties else None,
            weight=weight,
            source=source
        )
        logger.info(f"创建关系成功: {relation_type} (ID: {relation.id})")
        return relation
    
    @handle_db_errors_with_reraise()
    def get_or_create_relation(self, source_entity_id: int, target_entity_id: int, 
                              relation_type: str, canonical_relation: Optional[str] = None,
                              properties: Optional[Dict[str, Any]] = None, weight: float = 1.0,
                              source: Optional[str] = None) -> Relation:
        """
        获取或创建关系
        
        Args:
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID
            relation_type: 关系类型
            canonical_relation: 规范关系类型
            properties: 关系属性
            weight: 关系权重
            source: 关系来源
            
        Returns:
            Relation: 获取或创建的关系对象
        """
        relation = self.relation_repo.get_or_create(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relation_type=relation_type,
            canonical_relation=canonical_relation,
            properties=json.dumps(properties) if properties else None,
            weight=weight,
            source=source
        )
        logger.debug(f"获取或创建关系: {relation_type} (ID: {relation.id})")
        return relation
    
    @handle_db_errors(default_return=[])
    def find_similar_relations(self, source_entity_id: int, target_entity_id: int, 
                              relation_type: str, threshold: float = 0.8) -> List[Relation]:
        """
        查找相似关系
        
        Args:
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID
            relation_type: 关系类型
            threshold: 相似度阈值
            
        Returns:
            List[Relation]: 相似的关系列表
        """
        # 查找相同实体对之间的所有关系
        relations = self.relation_repo.find_by_entities(source_entity_id, target_entity_id)
        
        # 过滤出相同类型的关系
        same_type_relations = [r for r in relations if r.relation_type == relation_type]
        
        # 这里可以添加更精确的相似度计算
        # 返回相似度大于阈值的关系
        return same_type_relations
    
    @handle_db_errors_with_reraise()
    def merge_relations(self, relation_ids: List[int], canonical_relation: str, 
                       description: Optional[str] = None) -> RelationGroup:
        """
        合并关系，创建关系分组
        
        Args:
            relation_ids: 要合并的关系ID列表
            canonical_relation: 合并后的规范关系类型
            description: 分组描述
            
        Returns:
            RelationGroup: 创建的关系分组对象
        """
        # 创建关系分组
        relation_group = self.relation_group_repo.create(
            group_name=canonical_relation,
            description=description
        )
        
        # 更新所有关系的分组ID和规范关系类型
        for relation_id in relation_ids:
            relation = self.relation_repo.get(relation_id)
            if relation:
                self.relation_repo.update(
                    relation_id,
                    relation_group_id=relation_group.id,
                    canonical_relation=canonical_relation
                )
        
        logger.info(f"合并关系成功: {canonical_relation}, 包含 {len(relation_ids)} 个关系")
        return relation_group
    
    @handle_db_errors(default_return=None)
    def get_relation_by_id(self, relation_id: int) -> Optional[Relation]:
        """根据ID获取关系"""
        return self.relation_repo.get(relation_id)
    
    @handle_db_errors(default_return=[])
    def get_relations_by_group(self, relation_group_id: int) -> List[Relation]:
        """根据分组ID获取关系"""
        return self.relation_repo.find_by_group_id(relation_group_id)
    
    @handle_db_errors(default_return=[])
    def get_relations_by_type(self, relation_type: str, limit: Optional[int] = None) -> List[Relation]:
        """根据类型获取关系"""
        return self.relation_repo.find_by_type(relation_type, limit)
    
    @handle_db_errors(default_return=[])
    def get_relations_by_entity(self, entity_id: int, as_source: bool = True, 
                               as_target: bool = True, relation_type: Optional[str] = None) -> List[Relation]:
        """
        根据实体ID获取关系
        
        Args:
            entity_id: 实体ID
            as_source: 是否作为源实体
            as_target: 是否作为目标实体
            relation_type: 关系类型过滤
            
        Returns:
            List[Relation]: 关系列表
        """
        relations = []
        
        if as_source:
            relations.extend(self.relation_repo.find_by_source_entity(entity_id, relation_type))
        
        if as_target:
            relations.extend(self.relation_repo.find_by_target_entity(entity_id, relation_type))
        
        return relations
    
    @handle_db_errors(default_return=[])
    def get_entity_relations(self, source_entity_id: int, target_entity_id: int) -> List[Relation]:
        """获取两个实体之间的关系"""
        return self.relation_repo.find_by_entities(source_entity_id, target_entity_id)
    
    @handle_db_errors(default_return=None)
    def update_relation(self, relation_id: int, **kwargs) -> Optional[Relation]:
        """更新关系"""
        if 'properties' in kwargs and kwargs['properties']:
            kwargs['properties'] = json.dumps(kwargs['properties'])
        return self.relation_repo.update(relation_id, **kwargs)


class NewsService:
    """新闻服务类，提供新闻相关的高级操作"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_db_session()
        self.news_repo = NewsRepository(self.session)
        self.entity_news_repo = EntityNewsRepository(self.session)
        self.entity_service = EntityService(self.session)
    
    @handle_db_errors_with_reraise()
    async def create_news(self, title: str, content: str, url: Optional[str] = None,
                   publish_time: Optional[datetime] = None, source: Optional[str] = None,
                   category: Optional[str] = None) -> News:
        """
        创建新闻
        
        Args:
            title: 新闻标题
            content: 新闻内容
            url: 新闻URL
            publish_time: 发布时间
            source: 新闻来源
            category: 新闻类别
            
        Returns:
            News: 创建的新闻对象
        """
        news = await self.news_repo.create(
            title=title,
            content=content,
            url=url,
            publish_time=publish_time,
            source=source,
            category=category
        )
        logger.info(f"创建新闻成功: {title} (ID: {news.id})")
        return news
    
    @handle_db_errors_with_reraise()
    def get_or_create_news(self, title: str, content: str, url: Optional[str] = None,
                          publish_time: Optional[datetime] = None, source: Optional[str] = None,
                          category: Optional[str] = None) -> News:
        """
        获取或创建新闻
        
        Args:
            title: 新闻标题
            content: 新闻内容
            url: 新闻URL
            publish_time: 发布时间
            source: 新闻来源
            category: 新闻类别
            
        Returns:
            News: 获取或创建的新闻对象
        """
        # 如果有URL，先根据URL查找
        if url:
            news = self.news_repo.find_by_url(url)
            if news:
                logger.debug(f"找到已存在新闻: {title} (ID: {news.id})")
                return news
        
        # 创建新新闻
        news = self.news_repo.create(
            title=title,
            content=content,
            url=url,
            publish_time=publish_time,
            source=source,
            category=category
        )
        logger.info(f"创建新新闻: {title} (ID: {news.id})")
        return news
    
    @handle_db_errors(default_return=None)
    async def get_news_by_id(self, news_id: int) -> Optional[News]:
        """根据ID获取新闻"""
        return await self.news_repo.get(news_id)
    
    @handle_db_errors(default_return=[])
    def get_news_by_status(self, status: str, limit: Optional[int] = None) -> List[News]:
        """根据提取状态获取新闻"""
        return self.news_repo.find_by_extraction_status(status, limit)
    
    @handle_db_errors(default_return=[])
    def get_recent_news(self, days: int = 7, limit: Optional[int] = None) -> List[News]:
        """获取最近几天的新闻"""
        return self.news_repo.get_recent_news(days, limit)
    
    @handle_db_errors(default_return=[])
    def search_news(self, keyword: str, limit: Optional[int] = None) -> List[News]:
        """搜索新闻"""
        return self.news_repo.search_news(keyword, limit)
    
    @handle_db_errors(default_return=None)
    def update_extraction_status(self, news_id: int, status: str) -> Optional[News]:
        """更新新闻的提取状态"""
        return self.news_repo.update(news_id, extraction_status=status, extracted_at=datetime.utcnow())
    
    @handle_db_errors_with_reraise()
    def link_entity_to_news(self, entity_id: int, news_id: int, 
                           context: Optional[str] = None) -> EntityNews:
        """
        将实体链接到新闻
        
        Args:
            entity_id: 实体ID
            news_id: 新闻ID
            context: 实体在新闻中的上下文
            
        Returns:
            EntityNews: 创建的实体-新闻关联对象
        """
        return self.entity_news_repo.get_or_create(
            entity_id=entity_id,
            news_id=news_id,
            context=context
        )
    
    @handle_db_errors(default_return=[])
    def get_news_entities(self, news_id: int, limit: Optional[int] = None) -> List[Entity]:
        """获取新闻中的实体"""
        # 获取新闻与实体的关联记录
        entity_news_list = self.entity_news_repo.find_by_news(news_id, limit)
        # 获取所有实体ID
        entity_ids = [en.entity_id for en in entity_news_list]
        # 获取实体对象
        entities = []
        for entity_id in entity_ids:
            entity = self.entity_service.get_entity_by_id(entity_id)
            if entity:
                entities.append(entity)
        return entities
    
    @handle_db_errors(default_return=None)
    def update_news(self, news_id: int, **kwargs) -> Optional[News]:
        """更新新闻"""
        return self.news_repo.update(news_id, **kwargs)


class KnowledgeGraphService:
    """
    知识图谱服务类，提供知识图谱的综合操作
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_db_session()
        self.entity_service = EntityService(self.session)
        self.relation_service = RelationService(self.session)
        self.news_service = NewsService(self.session)
    
    @handle_db_errors_with_reraise()
    async def create_news(self, title: str, content: str, source: str = "unknown", publish_time: Optional[datetime] = None, author: str = None, url: str = None) -> News:
        """
        创建新闻
        
        Args:
            title: 新闻标题
            content: 新闻内容
            source: 新闻来源（默认：unknown）
            publish_time: 发布时间（默认：当前时间）
            author: 作者（可选）
            url: 新闻URL（可选）
            
        Returns:
            News: 创建的新闻对象
        """
        return await self.news_service.create_news(title, content, url, publish_time, source)
    
    @handle_db_errors(default_return=(None, [], []))
    async def store_llm_extracted_data(self, news_id: int, entities: List[Dict[str, Any]], relations: List[Dict[str, Any]]) -> Tuple[Optional[News], List[Entity], List[Relation]]:
        """
        存储LLM提取的实体和关系到数据库
        
        Args:
            news_id: 新闻ID
            entities: LLM提取的实体列表
            relations: LLM提取的关系列表
            
        Returns:
            Tuple[Optional[News], List[Entity], List[Relation]]: 新闻对象、存储的实体列表、存储的关系列表
        """
        logger.info(f"开始存储LLM提取的数据，新闻ID: {news_id}")
        
        # 获取或创建新闻
        news = await self.news_service.get_news_by_id(news_id)
        if not news:
            logger.error(f"新闻不存在，新闻ID: {news_id}")
            return (None, [], [])
        
        # 存储实体并建立映射关系
        stored_entities = []
        entity_map = {}  # 用于将实体名称映射到ID
        
        for entity in entities:
            entity_name = entity.get("name")
            entity_type = entity.get("type", "entity")
            confidence = entity.get("confidence", 1.0)
            properties = entity.copy()
            properties.pop("name", None)
            properties.pop("type", None)
            properties.pop("confidence", None)
            
            if entity_name and entity_type:
                # 获取或创建实体
                db_entity = self.entity_service.get_or_create_entity(
                    name=entity_name,
                    entity_type=entity_type,
                    properties=properties,
                    confidence_score=confidence,
                    source="llm"
                )
                stored_entities.append(db_entity)
                entity_map[entity_name] = db_entity.id
                
                # 建立实体与新闻的关联
                self.news_service.link_entity_to_news(news_id, db_entity.id)
        
        logger.info(f"存储实体完成，共 {len(stored_entities)} 个实体")
        
        # 存储关系
        stored_relations = []
        
        for relation in relations:
            source_name = relation.get("source_entity")
            target_name = relation.get("target_entity")
            relation_type = relation.get("relation_type")
            confidence = relation.get("confidence", 1.0)
            
            if source_name and target_name and relation_type:
                source_id = entity_map.get(source_name)
                target_id = entity_map.get(target_name)
                
                if source_id and target_id:
                    # 使用get_or_create_relation方法，自动检查并创建关系
                    new_relation = self.relation_service.get_or_create_relation(
                        source_entity_id=source_id,
                        target_entity_id=target_id,
                        relation_type=relation_type,
                        properties=relation,
                        weight=confidence,
                        source="llm"
                    )
                    stored_relations.append(new_relation)
        logger.info(f"存储关系完成，共 {len(stored_relations)} 个关系")
        
        # 更新新闻状态为已提取
        self.news_service.update_news(news_id, extraction_status="completed", extracted_at=datetime.now(timezone.utc))
        
        logger.info(f"存储LLM提取的数据完成，新闻ID: {news_id}")
        return (news, stored_entities, stored_relations)
    
    @handle_db_errors_with_reraise()
    def extract_and_store_entities(self, news_id: int, entities: List[Dict[str, Any]]) -> List[Entity]:
        """
        从新闻中提取并存储实体
        
        Args:
            news_id: 新闻ID
            entities: 实体列表，每个实体包含name、type等属性
            
        Returns:
            List[Entity]: 创建或获取的实体列表
        """
        logger.info(f"开始从新闻 {news_id} 中提取并存储 {len(entities)} 个实体")
        stored_entities = []
        
        for entity_data in entities:
            # 获取或创建实体
            entity = self.entity_service.get_or_create_entity(
                name=entity_data.get('name'),
                entity_type=entity_data.get('type'),
                canonical_name=entity_data.get('canonical_name'),
                properties=entity_data.get('properties'),
                confidence_score=entity_data.get('confidence_score', 0.0),
                source=entity_data.get('source')
            )
            
            # 将实体链接到新闻
            self.news_service.link_entity_to_news(
                entity_id=entity.id,
                news_id=news_id,
                context=entity_data.get('context')
            )
            
            stored_entities.append(entity)
        
        logger.info(f"成功从新闻 {news_id} 中提取并存储 {len(stored_entities)} 个实体")
        return stored_entities
    
    @handle_db_errors_with_reraise()
    def extract_and_store_relations(self, news_id: int, relations: List[Dict[str, Any]]) -> List[Relation]:
        """
        从新闻中提取并存储关系
        
        Args:
            news_id: 新闻ID
            relations: 关系列表，每个关系包含source_entity、target_entity、type等属性
            
        Returns:
            List[Relation]: 创建或获取的关系列表
        """
        logger.info(f"开始从新闻 {news_id} 中提取并存储 {len(relations)} 个关系")
        stored_relations = []
        
        for relation_data in relations:
            # 获取或创建源实体和目标实体
            source_entity = self.entity_service.get_or_create_entity(
                name=relation_data.get('source_entity').get('name'),
                entity_type=relation_data.get('source_entity').get('type'),
                canonical_name=relation_data.get('source_entity').get('canonical_name'),
                properties=relation_data.get('source_entity').get('properties'),
                confidence_score=relation_data.get('source_entity').get('confidence_score', 0.0),
                source=relation_data.get('source_entity').get('source')
            )
            
            target_entity = self.entity_service.get_or_create_entity(
                name=relation_data.get('target_entity').get('name'),
                entity_type=relation_data.get('target_entity').get('type'),
                canonical_name=relation_data.get('target_entity').get('canonical_name'),
                properties=relation_data.get('target_entity').get('properties'),
                confidence_score=relation_data.get('target_entity').get('confidence_score', 0.0),
                source=relation_data.get('target_entity').get('source')
            )
            
            # 获取或创建关系
            relation = self.relation_service.get_or_create_relation(
                source_entity_id=source_entity.id,
                target_entity_id=target_entity.id,
                relation_type=relation_data.get('type'),
                canonical_relation=relation_data.get('canonical_type'),
                properties=relation_data.get('properties'),
                weight=relation_data.get('weight', 1.0),
                source=relation_data.get('source')
            )
            
            # 将源实体和目标实体链接到新闻
            self.news_service.link_entity_to_news(
                entity_id=source_entity.id,
                news_id=news_id,
                context=relation_data.get('context')
            )
            
            self.news_service.link_entity_to_news(
                entity_id=target_entity.id,
                news_id=news_id,
                context=relation_data.get('context')
            )
            
            stored_relations.append(relation)
        
        logger.info(f"成功从新闻 {news_id} 中提取并存储 {len(stored_relations)} 个关系")
        return stored_relations
    
    @handle_db_errors_with_reraise()
    def process_news(self, news_id: int, entities: List[Dict[str, Any]], 
                    relations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理新闻，提取并存储实体和关系
        
        Args:
            news_id: 新闻ID
            entities: 实体列表
            relations: 关系列表
            
        Returns:
            Dict[str, Any]: 处理结果，包含实体和关系的数量
        """
        logger.info(f"开始处理新闻 {news_id}，包含 {len(entities)} 个实体和 {len(relations)} 个关系")
        
        # 提取并存储实体
        stored_entities = self.extract_and_store_entities(news_id, entities)
        
        # 提取并存储关系
        stored_relations = self.extract_and_store_relations(news_id, relations)
        
        # 更新新闻的提取状态
        self.news_service.update_extraction_status(news_id, 'completed')
        
        result = {
            'news_id': news_id,
            'entities_count': len(stored_entities),
            'relations_count': len(stored_relations),
            'entities': [entity.id for entity in stored_entities],
            'relations': [relation.id for relation in stored_relations]
        }
        
        logger.info(f"成功处理新闻 {news_id}，提取了 {len(stored_entities)} 个实体和 {len(stored_relations)} 个关系")
        return result
    
    @handle_db_errors(default_return={})
    def get_entity_neighbors(self, entity_id: int, max_depth: int = 1) -> Dict[str, Any]:
        """
        获取实体的邻居节点
        
        Args:
            entity_id: 实体ID
            max_depth: 最大深度
            
        Returns:
            Dict[str, Any]: 邻居节点信息
        """
        logger.info(f"开始获取实体 {entity_id} 的邻居节点，最大深度: {max_depth}")
        
        # 获取实体信息
        entity = self.entity_service.get_entity_by_id(entity_id)
        if not entity:
            logger.warning(f"未找到实体 {entity_id}")
            return {}
        
        # 初始化结果
        result = {
            'entity': entity.to_dict(),
            'neighbors': {},
            'relations': []
        }
        
        # 使用BFS获取邻居节点
        visited = {entity_id}
        queue = [(entity_id, 0)]  # (entity_id, depth)
        
        while queue:
            current_entity_id, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            # 获取当前实体的所有关系
            relations = self.relation_service.get_relations_by_entity(current_entity_id)
            
            for relation in relations:
                # 确定邻居实体ID
                neighbor_id = relation.target_entity_id if relation.source_entity_id == current_entity_id else relation.source_entity_id
                
                # 如果邻居节点未访问过，添加到队列
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1))
                    
                    # 获取邻居实体信息
                    neighbor_entity = self.entity_service.get_entity_by_id(neighbor_id)
                    if neighbor_entity:
                        result['neighbors'][neighbor_id] = {
                            'entity': neighbor_entity.to_dict(),
                            'depth': depth + 1
                        }
                
                # 添加关系信息
                result['relations'].append({
                    'id': relation.id,
                    'source_entity_id': relation.source_entity_id,
                    'target_entity_id': relation.target_entity_id,
                    'relation_type': relation.relation_type,
                    'weight': relation.weight,
                    'properties': relation.properties
                })
        
        logger.info(f"成功获取实体 {entity_id} 的邻居节点，共找到 {len(result['neighbors'])} 个邻居")
        return result
    
    @handle_db_errors(default_return=[])
    def deduplicate_entities(self, similarity_threshold: float = 0.8) -> List[EntityGroup]:
        """
        实体去重
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            List[EntityGroup]: 创建的实体分组列表
        """
        logger.info(f"开始进行实体去重，相似度阈值: {similarity_threshold}")
        
        # 这里实现实体去重的逻辑
        # 可以使用各种相似度计算方法，如编辑距离、语义相似度等
        
        # 简化实现：按类型和名称前缀分组
        entity_groups = []
        
        # 获取所有实体
        all_entities = self.entity_service.entity_repo.get_all()
        logger.info(f"获取到 {len(all_entities)} 个实体进行去重")
        
        # 按类型分组
        entities_by_type = {}
        for entity in all_entities:
            entity_type = entity.type
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        # 对每种类型的实体进行去重
        for entity_type, entities in entities_by_type.items():
            logger.debug(f"对 {entity_type} 类型的 {len(entities)} 个实体进行去重")
            
            # 这里可以使用更复杂的聚类算法
            # 简化实现：按名称前缀分组
            name_prefixes = {}
            
            for entity in entities:
                # 使用名称的前2个字符作为前缀
                prefix = entity.name[:2]
                if prefix not in name_prefixes:
                    name_prefixes[prefix] = []
                name_prefixes[prefix].append(entity)
            
            # 对每个前缀分组进行合并
            for prefix, group_entities in name_prefixes.items():
                if len(group_entities) > 1:
                    # 选择置信度最高的实体作为主要实体
                    primary_entity = max(group_entities, key=lambda e: e.confidence_score)
                    
                    # 创建实体分组
                    entity_group = self.entity_service.merge_entities(
                        entity_ids=[e.id for e in group_entities],
                        canonical_name=primary_entity.name,
                        description=f"合并自前缀为'{prefix}'的{entity_type}实体"
                    )
                    
                    entity_groups.append(entity_group)
        
        logger.info(f"完成实体去重，创建了 {len(entity_groups)} 个实体分组")
        return entity_groups
    
    @handle_db_errors(default_return=[])
    def deduplicate_relations(self, similarity_threshold: float = 0.8) -> List[RelationGroup]:
        """
        关系去重
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            List[RelationGroup]: 创建的关系分组列表
        """
        logger.info(f"开始进行关系去重，相似度阈值: {similarity_threshold}")
        
        # 获取所有关系
        all_relations = self.relation_service.relation_repo.get_all()
        logger.info(f"获取到 {len(all_relations)} 个关系进行去重")
        
        # 按实体对分组
        entity_pairs = {}
        
        for relation in all_relations:
            # 创建实体对的键（排序后确保一致性）
            source_id = relation.source_entity_id
            target_id = relation.target_entity_id
            
            # 确保source_id <= target_id，以便统一排序
            if source_id > target_id:
                source_id, target_id = target_id, source_id
            
            pair_key = f"{source_id}_{target_id}"
            
            if pair_key not in entity_pairs:
                entity_pairs[pair_key] = []
            entity_pairs[pair_key].append(relation)
        
        # 对每个实体对的关系进行去重
        relation_groups = []
        for pair_key, relations in entity_pairs.items():
            if len(relations) > 1:
                # 按关系类型分组
                relation_types = {}
                
                for relation in relations:
                    relation_type = relation.relation_type
                    if relation_type not in relation_types:
                        relation_types[relation_type] = []
                    relation_types[relation_type].append(relation)
                
                # 对每种关系类型进行合并
                for relation_type, type_relations in relation_types.items():
                    if len(type_relations) > 1:
                        # 选择权重最高的关系作为主要关系
                        primary_relation = max(type_relations, key=lambda r: r.weight)
                        
                        # 创建关系分组
                        relation_group = self.relation_service.merge_relations(
                            relation_ids=[r.id for r in type_relations],
                            canonical_relation=relation_type,
                            description=f"合并自实体对{pair_key}的{relation_type}关系"
                        )
                        
                        relation_groups.append(relation_group)
        
        logger.info(f"完成关系去重，创建了 {len(relation_groups)} 个关系分组")
        return relation_groups
    
    @handle_db_errors(default_return={})
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取知识图谱统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        logger.info("开始获取知识图谱统计信息")
        
        # 获取实体统计
        entity_count = self.entity_service.entity_repo.count()
        entity_type_counts = self.entity_service.entity_repo.count_by_type()
        
        # 获取关系统计
        relation_count = self.relation_service.relation_repo.count()
        relation_type_counts = self.relation_service.relation_repo.count_by_type()
        
        # 获取新闻统计
        news_count = self.news_service.news_repo.count()
        news_status_counts = self.news_service.news_repo.count_by_status()
        
        # 获取实体组统计
        entity_group_count = self.entity_service.entity_group_repo.count()
        
        # 获取关系组统计
        relation_group_count = self.relation_service.relation_group_repo.count()
        
        statistics = {
            'entities': {
                'total': entity_count,
                'by_type': entity_type_counts
            },
            'relations': {
                'total': relation_count,
                'by_type': relation_type_counts
            },
            'news': {
                'total': news_count,
                'by_status': news_status_counts
            },
            'entity_groups': entity_group_count,
            'relation_groups': relation_group_count
        }
        
        logger.info(f"获取知识图谱统计信息完成，实体: {entity_count}, 关系: {relation_count}, 新闻: {news_count}")
        return statistics