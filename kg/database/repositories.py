"""
数据仓库层模块

提供对数据库表的基本CRUD操作
"""
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Union
from sqlalchemy import desc, asc, or_, and_, func, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .models import Entity, Relation, News, EntityNews, EntityGroup, RelationGroup
from .connection import get_db_session
from ..utils.db_utils import handle_db_errors, handle_db_errors_with_reraise

# 配置日志
logger = logging.getLogger(__name__)


class BaseRepository:
    """基础仓库类，提供通用的CRUD操作"""
    
    def __init__(self, model_class, session: Optional[Session] = None):
        self.model_class = model_class
        self.session = session or get_db_session()
    
    @handle_db_errors(default_return=None)
    async def get(self, id: int) -> Optional[Any]:
        """根据ID获取单个记录"""
        return await self.session.query(self.model_class).filter(self.model_class.id == id).first()
    
    @handle_db_errors(default_return=[])
    async def get_all(self, limit: Optional[int] = None) -> List[Any]:
        """获取所有记录"""
        query = self.session.query(self.model_class)
        if limit:
            query = query.limit(limit)
        return await query.all()
    
    @handle_db_errors_with_reraise()
    async def create(self, **kwargs) -> Any:
        """创建新记录"""
        # 处理properties字段，如果是字典则转换为JSON字符串
        if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
            kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
            
        instance = self.model_class(**kwargs)
        await self.session.add(instance)
        await self.session.flush()
        return instance
    
    @handle_db_errors_with_reraise()
    async def update(self, id: int, **kwargs) -> Optional[Any]:
        """更新记录"""
        # 处理properties字段，如果是字典则转换为JSON字符串
        if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
            kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
            
        instance = await self.get(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await self.session.flush()
        return instance
    
    @handle_db_errors_with_reraise()
    async def delete(self, id: int) -> bool:
        """删除记录"""
        instance = await self.get(id)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
            return True
        return False
    
    @handle_db_errors(default_return=[])
    def find_by(self, **kwargs) -> List[Any]:
        """根据条件查找记录"""
        query = self.session.query(self.model_class)
        for key, value in kwargs.items():
            query = query.filter(getattr(self.model_class, key) == value)
        return query.all()
    
    @handle_db_errors(default_return=None)
    def find_one_by(self, **kwargs) -> Optional[Any]:
        """根据条件查找单个记录"""
        query = self.session.query(self.model_class)
        for key, value in kwargs.items():
            query = query.filter(getattr(self.model_class, key) == value)
        return query.first()


class EntityRepository(BaseRepository):
    """实体仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(Entity, session)
    
    @handle_db_errors(default_return=[])
    def find_by_name(self, name: str, entity_type: Optional[str] = None) -> List[Entity]:
        """根据名称查找实体"""
        query = self.session.query(Entity).filter(Entity.name == name)
        if entity_type:
            query = query.filter(Entity.type == entity_type)
        return query.all()
    
    @handle_db_errors(default_return=[])
    def find_by_canonical_name(self, canonical_name: str) -> List[Entity]:
        """根据规范名称查找实体"""
        return self.session.query(Entity).filter(Entity.canonical_name == canonical_name).all()
    
    @handle_db_errors(default_return=[])
    def find_by_group_id(self, entity_group_id: int) -> List[Entity]:
        """根据分组ID查找实体"""
        return self.session.query(Entity).filter(Entity.entity_group_id == entity_group_id).all()
    
    @handle_db_errors(default_return=[])
    def find_by_type(self, entity_type: str, limit: Optional[int] = None) -> List[Entity]:
        """根据类型查找实体"""
        query = self.session.query(Entity).filter(Entity.type == entity_type)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @handle_db_errors(default_return=[])
    def search_entities(self, keyword: str, entity_type: Optional[str] = None, 
                        limit: Optional[int] = None) -> List[Entity]:
        """搜索实体（名称或规范名称包含关键词）"""
        query = self.session.query(Entity).filter(
            or_(Entity.name.like(f'%{keyword}%'), 
                Entity.canonical_name.like(f'%{keyword}%'))
        )
        if entity_type:
            query = query.filter(Entity.type == entity_type)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @handle_db_errors_with_reraise()
    def get_or_create(self, name: str, entity_type: str, **kwargs) -> Entity:
        """获取或创建实体"""
        entity = self.session.query(Entity).filter(
            and_(Entity.name == name, Entity.type == entity_type)
        ).first()
        
        if not entity:
            # 处理properties字段，如果是字典则转换为JSON字符串
            if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
                kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
            
            entity = Entity(name=name, type=entity_type, **kwargs)
            self.session.add(entity)
            self.session.flush()
            logger.debug(f"创建新实体: {name}, 类型: {entity_type}")
        return entity


class RelationRepository(BaseRepository):
    """关系仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(Relation, session)
    
    @handle_db_errors(default_return=[])
    def find_by_entities(self, source_entity_id: int, target_entity_id: int, 
                         relation_type: Optional[str] = None) -> List[Relation]:
        """根据实体ID查找关系"""
        query = self.session.query(Relation).filter(
            and_(Relation.source_entity_id == source_entity_id, 
                 Relation.target_entity_id == target_entity_id)
        )
        if relation_type:
            query = query.filter(Relation.relation_type == relation_type)
        return query.all()
    
    @handle_db_errors(default_return=[])
    def find_by_source_entity(self, source_entity_id: int, relation_type: Optional[str] = None) -> List[Relation]:
        """根据源实体ID查找关系"""
        query = self.session.query(Relation).filter(Relation.source_entity_id == source_entity_id)
        if relation_type:
            query = query.filter(Relation.relation_type == relation_type)
        return query.all()
    
    @handle_db_errors(default_return=[])
    def find_by_target_entity(self, target_entity_id: int, relation_type: Optional[str] = None) -> List[Relation]:
        """根据目标实体ID查找关系"""
        query = self.session.query(Relation).filter(Relation.target_entity_id == target_entity_id)
        if relation_type:
            query = query.filter(Relation.relation_type == relation_type)
        return query.all()
    
    @handle_db_errors(default_return=[])
    def find_by_type(self, relation_type: str, limit: Optional[int] = None) -> List[Relation]:
        """根据关系类型查找关系"""
        query = self.session.query(Relation).filter(Relation.relation_type == relation_type)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @handle_db_errors(default_return=[])
    def find_by_group_id(self, relation_group_id: int) -> List[Relation]:
        """根据分组ID查找关系"""
        return self.session.query(Relation).filter(Relation.relation_group_id == relation_group_id).all()
    
    @handle_db_errors(default_return=[])
    def find_by_canonical_relation(self, canonical_relation: str) -> List[Relation]:
        """根据规范关系类型查找关系"""
        return self.session.query(Relation).filter(Relation.canonical_relation == canonical_relation).all()
    
    @handle_db_errors_with_reraise()
    def get_or_create(self, source_entity_id: int, target_entity_id: int, 
                     relation_type: str, **kwargs) -> Relation:
        """获取或创建关系"""
        relation = self.session.query(Relation).filter(
            and_(Relation.source_entity_id == source_entity_id, 
                 Relation.target_entity_id == target_entity_id,
                 Relation.relation_type == relation_type)
        ).first()
        
        if not relation:
            # 处理properties字段
            if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
                kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
            
            relation = Relation(
                source_entity_id=source_entity_id,
                target_entity_id=target_entity_id,
                relation_type=relation_type,
                **kwargs
            )
            self.session.add(relation)
            self.session.flush()
            logger.debug(f"创建新关系: {source_entity_id} -> {target_entity_id}, 类型: {relation_type}")
        return relation


class NewsRepository(BaseRepository):
    """新闻仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(News, session)
    
    @handle_db_errors(default_return=None)
    def find_by_url(self, url: str) -> Optional[News]:
        """根据URL查找新闻"""
        return self.session.query(News).filter(News.url == url).first()
    
    @handle_db_errors(default_return=[])
    def find_by_source(self, source: str, limit: Optional[int] = None) -> List[News]:
        """根据来源查找新闻"""
        query = self.session.query(News).filter(News.source == source)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @handle_db_errors(default_return=[])
    def find_by_category(self, category: str, limit: Optional[int] = None) -> List[News]:
        """根据类别查找新闻"""
        query = self.session.query(News).filter(News.category == category)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @handle_db_errors(default_return=[])
    def find_by_extraction_status(self, status: str, limit: Optional[int] = None) -> List[News]:
        """根据提取状态查找新闻"""
        query = self.session.query(News).filter(News.extraction_status == status)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @handle_db_errors(default_return=[])
    def search_news(self, keyword: str, limit: Optional[int] = None) -> List[News]:
        """搜索新闻（标题或内容包含关键词）"""
        query = self.session.query(News).filter(
            or_(News.title.like(f'%{keyword}%'), 
                News.content.like(f'%{keyword}%'))
        )
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @handle_db_errors(default_return=[])
    def get_recent_news(self, days: int = 7, limit: Optional[int] = None) -> List[News]:
        """获取最近几天的新闻"""
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        query = self.session.query(News).filter(News.publish_time >= start_date).order_by(desc(News.publish_time))
        if limit:
            query = query.limit(limit)
        return query.all()


class EntityNewsRepository(BaseRepository):
    """实体-新闻关联仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(EntityNews, session)
    
    @handle_db_errors(default_return=[])
    def find_by_entity(self, entity_id: int, limit: Optional[int] = None) -> List[EntityNews]:
        """根据实体ID查找关联"""
        query = self.session.query(EntityNews).filter(EntityNews.entity_id == entity_id)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @handle_db_errors(default_return=[])
    def find_by_news(self, news_id: int, limit: Optional[int] = None) -> List[EntityNews]:
        """根据新闻ID查找关联"""
        query = self.session.query(EntityNews).filter(EntityNews.news_id == news_id)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @handle_db_errors(default_return=None)
    def find_by_entity_and_news(self, entity_id: int, news_id: int) -> Optional[EntityNews]:
        """根据实体ID和新闻ID查找关联"""
        return self.session.query(EntityNews).filter(
            and_(EntityNews.entity_id == entity_id, EntityNews.news_id == news_id)
        ).first()
    
    @handle_db_errors_with_reraise()
    def get_or_create(self, entity_id: int, news_id: int, **kwargs) -> EntityNews:
        """获取或创建实体-新闻关联"""
        entity_news = self.find_by_entity_and_news(entity_id, news_id)
        
        if not entity_news:
            entity_news = EntityNews(
                entity_id=entity_id,
                news_id=news_id,
                **kwargs
            )
            self.session.add(entity_news)
            self.session.flush()
            logger.debug(f"创建新实体-新闻关联: entity_id={entity_id}, news_id={news_id}")
        
        return entity_news


class EntityGroupRepository(BaseRepository):
    """实体分组仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(EntityGroup, session)
    
    @handle_db_errors(default_return=[])
    def find_by_name(self, group_name: str) -> List[EntityGroup]:
        """根据分组名称查找分组"""
        return self.session.query(EntityGroup).filter(EntityGroup.group_name == group_name).all()
    
    @handle_db_errors(default_return=[])
    def find_by_primary_entity(self, primary_entity_id: int) -> List[EntityGroup]:
        """根据主要实体ID查找分组"""
        return self.session.query(EntityGroup).filter(EntityGroup.primary_entity_id == primary_entity_id).all()
    
    @handle_db_errors_with_reraise()
    def get_or_create(self, group_name: str, **kwargs) -> EntityGroup:
        """获取或创建实体分组"""
        entity_group = self.session.query(EntityGroup).filter(EntityGroup.group_name == group_name).first()
        
        if not entity_group:
            entity_group = EntityGroup(group_name=group_name, **kwargs)
            self.session.add(entity_group)
            self.session.flush()
            logger.debug(f"创建新实体分组: {group_name}")
        
        return entity_group


class RelationGroupRepository(BaseRepository):
    """关系分组仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(RelationGroup, session)
    
    @handle_db_errors(default_return=[])
    def find_by_name(self, group_name: str) -> List[RelationGroup]:
        """根据分组名称查找分组"""
        return self.session.query(RelationGroup).filter(RelationGroup.group_name == group_name).all()
    
    @handle_db_errors(default_return=[])
    def find_by_parent_id(self, parent_id: Optional[int]) -> List[RelationGroup]:
        """根据父组ID查找子组"""
        if parent_id is None:
            return self.session.query(RelationGroup).filter(RelationGroup.parent_id.is_(None)).all()
        return self.session.query(RelationGroup).filter(RelationGroup.parent_id == parent_id).all()
    
    @handle_db_errors(default_return=[])
    def get_root_groups(self) -> List[RelationGroup]:
        """获取根级关系组"""
        return self.session.query(RelationGroup).filter(RelationGroup.parent_id.is_(None)).all()
    
    @handle_db_errors_with_reraise()
    def get_or_create(self, group_name: str, parent_id: Optional[int] = None, **kwargs) -> RelationGroup:
        """获取或创建关系分组"""
        relation_group = self.session.query(RelationGroup).filter(RelationGroup.group_name == group_name).first()
        
        if not relation_group:
            relation_group = RelationGroup(
                group_name=group_name,
                parent_id=parent_id,
                **kwargs
            )
            self.session.add(relation_group)
            self.session.flush()
            logger.debug(f"创建新关系分组: {group_name}, parent_id={parent_id}")
        
        return relation_group
      
    
    def get_or_create(self, entity_id: int, news_id: int, **kwargs) -> EntityNews:
        """获取或创建实体-新闻关联"""
        try:
            entity_news = self.find_by_entity_and_news(entity_id, news_id)
            
            if not entity_news:
                # 处理properties字段，如果是字典则转换为JSON字符串
                if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
                    kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
                
                entity_news = EntityNews(
                    entity_id=entity_id,
                    news_id=news_id,
                    **kwargs
                )
                self.session.add(entity_news)
                self.session.flush()
                logger.debug(f"创建新实体-新闻关联: entity_id={entity_id}, news_id={news_id}")
            else:
                # 更新出现次数
                entity_news.occurrence_count += 1
                self.session.flush()
            
            return entity_news
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"获取或创建实体-新闻关联失败，entity_id: {entity_id}, news_id: {news_id}, 错误: {e}")
            raise
    
    def get_news_by_entity(self, entity_id: int, limit: Optional[int] = None) -> List[News]:
        """根据实体ID获取相关新闻"""
        try:
            query = self.session.query(News).join(EntityNews).filter(EntityNews.entity_id == entity_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"根据实体ID获取相关新闻失败，entity_id: {entity_id}, 错误: {e}")
            return []
    
    def get_entities_by_news(self, news_id: int, limit: Optional[int] = None) -> List[Entity]:
        """根据新闻ID获取相关实体"""
        try:
            query = self.session.query(Entity).join(EntityNews).filter(EntityNews.news_id == news_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"根据新闻ID获取相关实体失败，news_id: {news_id}, 错误: {e}")
            return []


class EntityGroupRepository(BaseRepository):
    """实体分组仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(EntityGroup, session)
    
    def find_by_name(self, group_name: str) -> Optional[EntityGroup]:
        """根据分组名称查找实体分组"""
        try:
            return self.session.query(EntityGroup).filter(EntityGroup.group_name == group_name).first()
        except SQLAlchemyError as e:
            logger.error(f"根据分组名称查找实体分组失败，group_name: {group_name}, 错误: {e}")
            return None
    
    def get_or_create(self, group_name: str, **kwargs) -> EntityGroup:
        """获取或创建实体分组"""
        try:
            entity_group = self.find_by_name(group_name)
            
            if not entity_group:
                # 处理properties字段，如果是字典则转换为JSON字符串
                if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
                    kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
                
                entity_group = EntityGroup(group_name=group_name, **kwargs)
                self.session.add(entity_group)
                self.session.flush()
                logger.debug(f"创建新实体分组: {group_name}")
            
            return entity_group
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"获取或创建实体分组失败，group_name: {group_name}, 错误: {e}")
            raise


class RelationGroupRepository(BaseRepository):
    """关系分组仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(RelationGroup, session)
    
    def find_by_name(self, group_name: str) -> Optional[RelationGroup]:
        """根据分组名称查找关系分组"""
        try:
            return self.session.query(RelationGroup).filter(RelationGroup.group_name == group_name).first()
        except SQLAlchemyError as e:
            logger.error(f"根据分组名称查找关系分组失败，group_name: {group_name}, 错误: {e}")
            return None
    
    def get_or_create(self, group_name: str, **kwargs) -> RelationGroup:
        """获取或创建关系分组"""
        try:
            relation_group = self.find_by_name(group_name)
            
            if not relation_group:
                # 处理properties字段，如果是字典则转换为JSON字符串
                if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
                    kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
                
                relation_group = RelationGroup(group_name=group_name, **kwargs)
                self.session.add(relation_group)
                self.session.flush()
                logger.debug(f"创建新关系分组: {group_name}")
            
            return relation_group
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"获取或创建关系分组失败，group_name: {group_name}, 错误: {e}")
            raise