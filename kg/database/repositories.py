"""
数据仓库层模块

提供对数据库表的基本CRUD操作
"""
import json
import logging
import inspect
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Union
from collections.abc import AsyncIterator
from sqlalchemy import desc, asc, or_, and_, func, text, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .models import Entity, Relation, News, EntityNews, EntityGroup, RelationGroup
from .connection import get_db_session, db_session
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
        """
        根据ID获取单个记录
        """
        stmt = select(self.model_class).where(self.model_class.id == id)
        if self.session and not isinstance(self.session, AsyncIterator):
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        else:
            async with db_session() as session:
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
    
    @handle_db_errors(default_return=[])
    async def get_all(self, limit: Optional[int] = None) -> List[Any]:
        """
        获取所有记录
        """
        stmt = select(self.model_class)
        if limit:
            stmt = stmt.limit(limit)
        if self.session and not isinstance(self.session, AsyncIterator) :
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            async with db_session() as session:
                result = await session.execute(stmt)
                return result.scalars().all()
    
    @handle_db_errors_with_reraise()
    async def create(self, **kwargs) -> Any:
        """创建新记录"""
        # 处理properties字段，如果是字典则转换为JSON字符串
        if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
            kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
            
        instance = self.model_class(**kwargs)
        if self.session and not isinstance(self.session, AsyncIterator):
            self.session.add(instance)
            await self.session.flush()
            return instance
        else:
            async with db_session() as session:
                session.add(instance)
                await session.flush()
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
            
            if self.session and not isinstance(self.session, AsyncIterator):
                await self.session.flush()
            else:
                async with db_session() as session:
                    await session.flush()
                    
        return instance
    
    @handle_db_errors_with_reraise()
    async def delete(self, id: int) -> bool:
        """删除记录"""
        instance = await self.get(id)
        if instance:
            if self.session and not isinstance(self.session, AsyncIterator):
                await self.session.delete(instance)
                await self.session.flush()
            else:
                async with db_session() as session:
                    await session.delete(instance)
                    await session.flush()
            return True
        return False
    
    @handle_db_errors_with_reraise()
    async def get_or_create(self, **kwargs) -> Tuple[Any, bool]:
        """
        查询或创建实体
        
        Args:
            **kwargs: 查询参数
        
        Returns:
            Tuple[Any, bool]: (实体, 是否创建)
        """
        # 处理properties字段，如果是字典则转换为JSON字符串
        if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
            kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)

        # 构建查询条件
        filters = []
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                filters.append(getattr(self.model_class, key) == value)
        
        stmt = select(self.model_class).filter(*filters)
        
        if self.session and not isinstance(self.session, AsyncIterator):
            # 使用提供的会话
            result = await self.session.execute(stmt)
            existing_instance = result.scalar_one_or_none()
            
            if existing_instance:
                return existing_instance, False
            
            # 创建新实体
            new_instance = self.model_class(**kwargs)
            self.session.add(new_instance)
            await self.session.flush()
            return new_instance, True
        else:
            # 创建新会话
            async with db_session() as session:
                result = await session.execute(stmt)
                existing_instance = result.scalar_one_or_none()
                
                if existing_instance:
                    return existing_instance, False
                
                # 创建新实体
                new_instance = self.model_class(**kwargs)
                session.add(new_instance)
                await session.flush()
                return new_instance, True

    @handle_db_errors(default_return=[])
    async def find_by(self, **kwargs) -> List[Any]:
        """根据条件查找记录"""
        stmt = select(self.model_class)
        for key, value in kwargs.items(): 
            stmt = stmt.where(getattr(self.model_class, key) == value)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=None)
    async def find_one_by(self, **kwargs) -> Optional[Any]:
        """根据条件查找单个记录"""
        stmt = select(self.model_class)
        for key, value in kwargs.items(): 
            stmt = stmt.where(getattr(self.model_class, key) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class EntityRepository(BaseRepository):
    """实体仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(Entity, session)
    
    @handle_db_errors(default_return=[])
    async def get_all_entity_types(self) -> List[str]:
        """
        获取所有不同的实体类型
        
        Returns:
            实体类型列表
        """
        stmt = select(Entity.type).distinct()
        if self.session and not isinstance(self.session, AsyncIterator):
            result = await self.session.execute(stmt)
            return [row[0] for row in result]
        else:
            async with db_session() as session:
                result = await session.execute(stmt)
                return [row[0] for row in result]
    
    @handle_db_errors(default_return=[]) 
    async def find_by_name(self, name: str, entity_type: Optional[str] = None) -> List[Entity]:
        """根据名称查找实体"""
        stmt = select(Entity).where(Entity.name == name)
        if entity_type:
            stmt = stmt.where(Entity.type == entity_type)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[])
    async def get_by_names(self, names: List[str]) -> List[Entity]:
        """根据名称列表批量获取实体"""
        if not names:
            return []
            
        stmt = select(Entity).where(Entity.name.in_(names))
        
        if self.session and not isinstance(self.session, AsyncIterator):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            async with db_session() as session:
                result = await session.execute(stmt)
                return result.scalars().all()
    
    @handle_db_errors(default_return=[]) 
    async def find_by_canonical_name(self, canonical_name: str) -> List[Entity]:
        """根据规范名称查找实体"""
        stmt = select(Entity).where(Entity.canonical_name == canonical_name)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[])
    async def find_by_group_id(self, entity_group_id: int) -> List[Entity]:
        """
        根据分组ID查找实体
        """
        stmt = select(Entity).filter(Entity.entity_group_id == entity_group_id)
        if self.session and not isinstance(self.session, AsyncIterator):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            async with db_session() as session:
                result = await session.execute(stmt)
                return result.scalars().all()
    
    @handle_db_errors(default_return=[])
    async def find_by_type(self, entity_type: str, limit: Optional[int] = None) -> List[Entity]:
        """根据类型查找实体"""
        stmt = select(Entity).where(Entity.type == entity_type)
        if limit:
            stmt = stmt.limit(limit)
        if self.session and not isinstance(self.session, AsyncIterator):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            async with db_session() as session:
                result = await session.execute(stmt)
                return result.scalars().all()
    
    @handle_db_errors(default_return=[])
    async def search_entities(self, keyword: str, entity_type: Optional[str] = None, 
                        limit: Optional[int] = None) -> List[Entity]:
        """搜索实体（名称或规范名称包含关键词）"""
        stmt = select(Entity).where(
            or_(Entity.name.like(f'%{keyword}%'), 
                Entity.canonical_name.like(f'%{keyword}%'))
        )
        if entity_type:
            stmt = stmt.where(Entity.type == entity_type)
        if limit:
            stmt = stmt.limit(limit)
        if self.session and not isinstance(self.session, AsyncIterator):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            async with db_session() as session:
                result = await session.execute(stmt)
                return result.scalars().all()
    
    @handle_db_errors_with_reraise()
    async def get_or_create(self, name: str, entity_type: str, **kwargs) -> Entity:
        """获取或创建实体"""
        from sqlalchemy import select
        stmt = select(Entity).where(
            and_(Entity.name == name, Entity.type == entity_type)
        )
        
        if self.session and not isinstance(self.session, AsyncIterator):
            # 使用提供的会话
            result = await self.session.execute(stmt)
            entity = result.scalar_one_or_none()
            
            if not entity:
                # 处理properties字段，如果是字典则转换为JSON字符串
                if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
                    kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
                
                entity = Entity(name=name, type=entity_type, **kwargs)
                self.session.add(entity)
                await self.session.flush()
                logger.debug(f"创建新实体: {name}, 类型: {entity_type}")
        else:
            # 创建新会话
            async with db_session() as session:
                result = await session.execute(stmt)
                entity = result.scalar_one_or_none()
                
                if not entity:
                    # 处理properties字段，如果是字典则转换为JSON字符串
                    if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
                        kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
                    
                    entity = Entity(name=name, type=entity_type, **kwargs)
                    session.add(entity)
                    await session.flush()
                    logger.debug(f"创建新实体: {name}, 类型: {entity_type}")
        
        return entity


class RelationRepository(BaseRepository):
    """关系仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(Relation, session)
    
    @handle_db_errors(default_return=[])
    async def get_all_relation_types(self) -> List[str]:
        """
        获取所有不同的关系类型
        
        Returns:
            关系类型列表
        """
        stmt = select(Relation.relation_type).distinct()
        if self.session and not isinstance(self.session, AsyncIterator):
            result = await self.session.execute(stmt)
            return [row[0] for row in result]
        else:
            async with db_session() as session:
                result = await session.execute(stmt)
                return [row[0] for row in result]
    
    @handle_db_errors(default_return=[]) 
    async def find_by_entities(self, source_entity_id: int, target_entity_id: int, 
                         relation_type: Optional[str] = None) -> List[Relation]:
        """根据实体ID查找关系"""
        stmt = select(Relation).where(
            and_(Relation.source_entity_id == source_entity_id, 
                 Relation.target_entity_id == target_entity_id)
        )
        if relation_type:
            stmt = stmt.where(Relation.relation_type == relation_type)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[])
    async def find_by_source_entity(self, source_entity_id: int, relation_type: Optional[str] = None) -> List[Relation]:
        """根据源实体ID查找关系"""
        stmt = select(Relation).where(Relation.source_entity_id == source_entity_id)
        if relation_type:
            stmt = stmt.where(Relation.relation_type == relation_type)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[])
    async def find_by_target_entity(self, target_entity_id: int, relation_type: Optional[str] = None) -> List[Relation]:
        """根据目标实体ID查找关系"""
        stmt = select(Relation).where(Relation.target_entity_id == target_entity_id)
        if relation_type:
            stmt = stmt.where(Relation.relation_type == relation_type)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[])
    async def find_by_type(self, relation_type: str, limit: Optional[int] = None) -> List[Relation]:
        """根据关系类型查找关系"""
        stmt = select(Relation).where(Relation.relation_type == relation_type)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[]) 
    async def find_by_group_id(self, relation_group_id: int) -> List[Relation]:
        """根据分组ID查找关系"""
        stmt = select(Relation).where(Relation.relation_group_id == relation_group_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[]) 
    async def find_by_canonical_relation(self, canonical_relation: str) -> List[Relation]:
        """根据规范关系类型查找关系"""
        stmt = select(Relation).where(Relation.canonical_relation == canonical_relation)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors_with_reraise()
    async def get_or_create(self, source_entity_id: int, target_entity_id: int, 
                     relation_type: str, **kwargs) -> Relation:
        """获取或创建关系"""
        from sqlalchemy import select
        stmt = select(Relation).where(
            and_(Relation.source_entity_id == source_entity_id, 
                 Relation.target_entity_id == target_entity_id,
                 Relation.relation_type == relation_type)
        )
        
        if self.session and not isinstance(self.session, AsyncIterator):
            # 使用提供的会话
            result = await self.session.execute(stmt)
            relation = result.scalar_one_or_none()
            
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
                await self.session.flush()
                logger.debug(f"创建新关系: {source_entity_id} -> {target_entity_id}, 类型: {relation_type}")
        else:
            # 创建新会话
            async with db_session() as session:
                result = await session.execute(stmt)
                relation = result.scalar_one_or_none()
                
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
                    session.add(relation)
                    await session.flush()
                    logger.debug(f"创建新关系: {source_entity_id} -> {target_entity_id}, 类型: {relation_type}")
        
        return relation


class NewsRepository(BaseRepository):
    """新闻仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(News, session)
    
    @handle_db_errors(default_return=None) 
    async def find_by_url(self, url: str) -> Optional[News]:
        """根据URL查找新闻"""
        stmt = select(News).where(News.url == url)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    @handle_db_errors(default_return=[]) 
    async def find_by_source(self, source: str, limit: Optional[int] = None) -> List[News]:
        """根据来源查找新闻"""
        stmt = select(News).where(News.source == source)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[]) 
    async def find_by_category(self, category: str, limit: Optional[int] = None) -> List[News]:
        """根据类别查找新闻"""
        stmt = select(News).where(News.category == category)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[]) 
    async def find_by_extraction_status(self, status: str, limit: Optional[int] = None) -> List[News]:
        """根据提取状态查找新闻"""
        stmt = select(News).where(News.extraction_status == status)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[]) 
    async def search_news(self, keyword: str, limit: Optional[int] = None) -> List[News]:
        """搜索新闻（标题或内容包含关键词）"""
        stmt = select(News).where(
            or_(News.title.like(f'%{keyword}%'), 
                News.content.like(f'%{keyword}%'))
        )
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[]) 
    async def get_recent_news(self, days: int = 7, limit: Optional[int] = None) -> List[News]:
        """获取最近几天的新闻"""
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        stmt = select(News).where(News.publish_time >= start_date).order_by(desc(News.publish_time))
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class EntityNewsRepository(BaseRepository):
    """实体-新闻关联仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(EntityNews, session)
    
    @handle_db_errors(default_return=[]) 
    async def find_by_entity(self, entity_id: int, limit: Optional[int] = None) -> List[EntityNews]:
        """根据实体ID查找关联"""
        stmt = select(EntityNews).where(EntityNews.entity_id == entity_id)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[]) 
    async def find_by_news(self, news_id: int, limit: Optional[int] = None) -> List[EntityNews]:
        """根据新闻ID查找关联"""
        stmt = select(EntityNews).where(EntityNews.news_id == news_id)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=None)
    async def find_by_entity_and_news(self, entity_id: int, news_id: int) -> Optional[EntityNews]:
        """根据实体ID和新闻ID查找关联"""
        stmt = select(EntityNews).filter(
            and_(EntityNews.entity_id == entity_id, EntityNews.news_id == news_id)
        )
        
        if self.session and not isinstance(self.session, AsyncIterator):
            # 使用提供的会话
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        else:
            # 创建新会话
            async with db_session() as session:
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
    
    @handle_db_errors_with_reraise()
    async def get_or_create(self, entity_id: int, news_id: int, **kwargs) -> EntityNews:
        """获取或创建实体-新闻关联"""
        entity_news = await self.find_by_entity_and_news(entity_id, news_id)
        
        if not entity_news:
            # 处理properties字段，如果是字典则转换为JSON字符串
            if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
                kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
            
            entity_news = EntityNews(
                entity_id=entity_id,
                news_id=news_id,
                **kwargs
            )
            
            if self.session and not isinstance(self.session, AsyncIterator):
                # 使用提供的会话
                self.session.add(entity_news)
                await self.session.flush()
                logger.debug(f"创建新实体-新闻关联: entity_id={entity_id}, news_id={news_id}")
            else:
                # 创建新会话
                async with db_session() as session:
                    session.add(entity_news)
                    await session.flush()
                    logger.debug(f"创建新实体-新闻关联: entity_id={entity_id}, news_id={news_id}")
        
        return entity_news


class EntityGroupRepository(BaseRepository):
    """实体分组仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(EntityGroup, session)
    
    @handle_db_errors(default_return=[])
    async def find_by_name(self, group_name: str) -> List[EntityGroup]:
        """根据分组名称查找分组"""
        stmt = select(EntityGroup).where(EntityGroup.group_name == group_name)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[])
    async def find_by_primary_entity(self, primary_entity_id: int) -> List[EntityGroup]:
        """根据主要实体ID查找分组"""
        stmt = select(EntityGroup).where(EntityGroup.primary_entity_id == primary_entity_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors_with_reraise()
    async def get_or_create(self, group_name: str, **kwargs) -> EntityGroup:
        """获取或创建实体分组"""
        stmt = select(EntityGroup).where(EntityGroup.group_name == group_name)
        result = await self.session.execute(stmt)
        entity_group = result.scalar_one_or_none()
        
        if not entity_group:
            entity_group = EntityGroup(group_name=group_name, **kwargs)
            self.session.add(entity_group)
            await self.session.flush()
            logger.debug(f"创建新实体分组: {group_name}")
        
        return entity_group


class RelationGroupRepository(BaseRepository):
    """关系分组仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(RelationGroup, session)
    
    @handle_db_errors(default_return=[]) 
    async def find_by_name(self, group_name: str) -> List[RelationGroup]:
        """根据分组名称查找分组"""
        stmt = select(RelationGroup).where(RelationGroup.group_name == group_name)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[]) 
    async def find_by_parent_id(self, parent_id: Optional[int]) -> List[RelationGroup]:
        """根据父组ID查找子组"""
        if parent_id is None:
            stmt = select(RelationGroup).where(RelationGroup.parent_id.is_(None))
        else:
            stmt = select(RelationGroup).where(RelationGroup.parent_id == parent_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors(default_return=[]) 
    async def get_root_groups(self) -> List[RelationGroup]:
        """获取根级关系组"""
        stmt = select(RelationGroup).where(RelationGroup.parent_id.is_(None))
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    @handle_db_errors_with_reraise() 
    async def get_or_create(self, group_name: str, parent_id: Optional[int] = None, **kwargs) -> RelationGroup:
        """获取或创建关系分组"""
        stmt = select(RelationGroup).where(RelationGroup.group_name == group_name)
        result = await self.session.execute(stmt)
        relation_group = result.scalar_one_or_none()
        
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
    
    async def get_news_by_entity(self, entity_id: int, limit: Optional[int] = None) -> List[News]:
        """根据实体ID获取相关新闻"""
        try:
            stmt = select(News).join(EntityNews).where(EntityNews.entity_id == entity_id)
            if limit:
                stmt = stmt.limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"根据实体ID获取相关新闻失败，entity_id: {entity_id}, 错误: {e}")
            return []
    
    async def get_entities_by_news(self, news_id: int, limit: Optional[int] = None) -> List[Entity]:
        """根据新闻ID获取相关实体"""
        try:
            stmt = select(Entity).join(EntityNews).where(EntityNews.news_id == news_id)
            if limit:
                stmt = stmt.limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"根据新闻ID获取相关实体失败，news_id: {news_id}, 错误: {e}")
            return []


class EntityGroupRepository(BaseRepository):
    """实体分组仓库类"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__(EntityGroup, session)
    
    async def find_by_name(self, group_name: str) -> Optional[EntityGroup]:
        """根据分组名称查找实体分组"""
        try:
            stmt = select(EntityGroup).where(EntityGroup.group_name == group_name)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"根据分组名称查找实体分组失败，group_name: {group_name}, 错误: {e}")
            return None
    
    async def get_or_create(self, group_name: str, **kwargs) -> EntityGroup:
        """获取或创建实体分组"""
        try:
            entity_group = await self.find_by_name(group_name)
            
            if not entity_group:
                # 处理properties字段，如果是字典则转换为JSON字符串
                if 'properties' in kwargs and isinstance(kwargs['properties'], dict):
                    kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
                
                entity_group = EntityGroup(group_name=group_name, **kwargs)
                self.session.add(entity_group)
                await self.session.flush()
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
    
    async def find_by_name(self, group_name: str) -> Optional[RelationGroup]:
        """根据分组名称查找关系分组"""
        try:
            stmt = select(RelationGroup).where(RelationGroup.group_name == group_name)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"根据分组名称查找关系分组失败，group_name: {group_name}, 错误: {e}")
            return None
    
    async def get_or_create(self, group_name: str, **kwargs) -> RelationGroup:
        """获取或创建关系分组"""
        try:
            relation_group = await self.find_by_name(group_name)
            
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