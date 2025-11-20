"""
实体操作存储库
包含具体的实体、关系、属性和新闻事件的操作逻辑
"""

import logging
from typing import List, Optional

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# 延迟导入模型，避免循环导入问题
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Entity, Relation, Attribute, NewsEvent, news_event_entity
    from sqlalchemy import Table
from .core import BaseRepository, DatabaseError, NotFoundError, IntegrityError as CoreIntegrityError

# 配置日志
logger = logging.getLogger(__name__)


class EntityRepository(BaseRepository):
    """实体存储库 - 包含具体的实体操作逻辑"""
    
    def __init__(self, session: AsyncSession):
        # 延迟导入模型
        from .models import Entity
        super().__init__(Entity, session)
    
    async def get_by_name(self, name: str):
        """根据名称获取实体"""
        try:
            from .models import Entity
            stmt = select(Entity).where(Entity.name == name)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"根据名称获取实体失败: {e}")
            raise DatabaseError(f"根据名称获取实体失败: {e}")
    
    async def get_by_type(self, entity_type: str, skip: int = 0, limit: int = 100):
        """根据类型获取实体"""
        try:
            from .models import Entity
            stmt = select(Entity).where(Entity.type == entity_type).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"根据类型获取实体失败: {e}")
            raise DatabaseError(f"根据类型获取实体失败: {e}")
    
    async def get_canonical_entity(self, entity_id: int):
        """获取实体的规范实体"""
        try:
            entity = await self.get_by_id(entity_id)
            if entity and entity.canonical_id:
                return await self.get_by_id(entity.canonical_id)
            return entity
        except SQLAlchemyError as e:
            logger.error(f"获取规范实体失败: {e}")
            raise DatabaseError(f"获取规范实体失败: {e}")
    
    async def merge_entities(self, from_entity_id: int, to_entity_id: int) -> bool:
        """合并实体 - 核心知识图谱操作"""
        try:
            from_entity = await self.get_by_id(from_entity_id)
            to_entity = await self.get_by_id(to_entity_id)
            
            if not from_entity or not to_entity:
                raise NotFoundError("实体未找到")
            
            # 更新from_entity的canonical_id
            from_entity.canonical_id = to_entity_id
            
            # 更新相关的relations
            relation_repo = RelationRepository(self.session)
            await relation_repo.update_entity_references(from_entity_id, to_entity_id)
            
            logger.info(f"实体合并成功: {from_entity_id} -> {to_entity_id}")
            return True
        except IntegrityError as e:
            logger.error(f"合并实体失败 - 完整性约束: {e}")
            raise CoreIntegrityError(f"合并实体失败 - 数据完整性约束: {e}")
        except SQLAlchemyError as e:
            logger.error(f"合并实体失败: {e}")
            raise DatabaseError(f"合并实体失败: {e}")
    
    async def get_by_canonical_id(self, canonical_id: int):
        """获取规范实体及其所有别名实体"""
        try:
            from sqlalchemy import or_
            from .models import Entity
            stmt = select(Entity).where(
                or_(
                    Entity.id == canonical_id,
                    Entity.canonical_id == canonical_id
                )
            ).order_by(Entity.id)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"获取规范实体失败: {e}")
            raise DatabaseError(f"获取规范实体失败: {e}")

    async def get_entity_relations(self, entity_id: int, skip: int = 0, limit: int = 100):
        """获取实体的所有关系"""
        try:
            relation_repo = RelationRepository(self.session)
            subject_relations = await relation_repo.get_by_subject(entity_id, skip, limit)
            object_relations = await relation_repo.get_by_object(entity_id, skip, limit)
            return subject_relations + object_relations
        except SQLAlchemyError as e:
            logger.error(f"获取实体关系失败: {e}")
            raise DatabaseError(f"获取实体关系失败: {e}")
    
    async def get_entity_attributes(self, entity_id: int):
        """获取实体的所有属性"""
        try:
            attribute_repo = AttributeRepository(self.session)
            return await attribute_repo.get_by_entity(entity_id)
        except SQLAlchemyError as e:
            logger.error(f"获取实体属性失败: {e}")
            raise DatabaseError(f"获取实体属性失败: {e}")
    

class RelationRepository(BaseRepository):
    """关系存储库 - 包含具体的关系操作逻辑"""
    
    def __init__(self, session: AsyncSession):
        # 延迟导入模型
        from .models import Relation
        super().__init__(Relation, session)
    
    async def get_by_subject(self, subject_id: int, skip: int = 0, limit: int = 100):
        """根据主体获取关系"""
        try:
            from .models import Relation
            stmt = select(Relation).where(Relation.subject_id == subject_id).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"根据主体获取关系失败: {e}")
            raise DatabaseError(f"根据主体获取关系失败: {e}")
    
    async def get_by_object(self, object_id: int, skip: int = 0, limit: int = 100):
        """根据客体获取关系"""
        try:
            from .models import Relation
            stmt = select(Relation).where(Relation.object_id == object_id).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"根据客体获取关系失败: {e}")
            raise DatabaseError(f"根据客体获取关系失败: {e}")
    
    async def get_by_predicate(self, predicate: str, skip: int = 0, limit: int = 100):
        """根据谓词获取关系"""
        try:
            from .models import Relation
            stmt = select(Relation).where(Relation.predicate == predicate).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"根据谓词获取关系失败: {e}")
            raise DatabaseError(f"根据谓词获取关系失败: {e}")
    
    async def get_triplets(self, subject_id: Optional[int] = None, predicate: Optional[str] = None, 
                          object_id: Optional[int] = None, skip: int = 0, limit: int = 100):
        """获取三元组 - 知识图谱核心查询"""
        try:
            from .models import Relation
            conditions = []
            if subject_id is not None:
                conditions.append(Relation.subject_id == subject_id)
            if predicate is not None:
                conditions.append(Relation.predicate == predicate)
            if object_id is not None:
                conditions.append(Relation.object_id == object_id)
            
            stmt = select(Relation)
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"获取三元组失败: {e}")
            raise DatabaseError(f"获取三元组失败: {e}")
    
    async def update_entity_references(self, old_entity_id: int, new_entity_id: int) -> bool:
        """更新实体引用 - 实体合并时的关键操作"""
        try:
            # 更新作为主体的关系
            stmt1 = update(Relation).where(Relation.subject_id == old_entity_id).values(subject_id=new_entity_id)
            await self.session.execute(stmt1)
            
            # 更新作为客体的关系
            stmt2 = update(Relation).where(Relation.object_id == old_entity_id).values(object_id=new_entity_id)
            await self.session.execute(stmt2)
            
            logger.info(f"实体引用更新成功: {old_entity_id} -> {new_entity_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"更新实体引用失败: {e}")
            raise DatabaseError(f"更新实体引用失败: {e}")
    
    async def get_relation_stats(self) -> dict:
        """获取关系统计信息"""
        try:
            from sqlalchemy import func
            
            # 统计不同谓词的数量
            stmt = select(Relation.predicate, func.count(Relation.id)).group_by(Relation.predicate)
            result = await self.session.execute(stmt)
            predicate_stats = dict(result.all())
            
            # 统计总关系数
            total_stmt = select(func.count(Relation.id))
            total_result = await self.session.execute(total_stmt)
            total_count = total_result.scalar()
            
            return {
                "total_relations": total_count,
                "predicate_distribution": predicate_stats
            }
        except SQLAlchemyError as e:
            logger.error(f"获取关系统计失败: {e}")
            raise DatabaseError(f"获取关系统计失败: {e}")
    
    async def find_redundant_relations(self):
        """查找冗余关系 - 知识图谱优化"""
        try:
            # 查找重复的三元组（主体、谓词、客体都相同）
            from sqlalchemy import func
            
            stmt = select(Relation).group_by(
                Relation.subject_id, Relation.predicate, Relation.object_id
            ).having(func.count(Relation.id) > 1)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"查找冗余关系失败: {e}")
            raise DatabaseError(f"查找冗余关系失败: {e}")


class AttributeRepository(BaseRepository):
    """属性存储库 - 包含具体的属性操作逻辑"""
    
    def __init__(self, session: AsyncSession):
        # 延迟导入模型
        from .models import Attribute
        super().__init__(Attribute, session)
    
    async def get_by_entity(self, entity_id: int):
        """根据实体获取属性"""
        try:
            from .models import Attribute
            stmt = select(Attribute).where(Attribute.entity_id == entity_id)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"根据实体获取属性失败: {e}")
            raise DatabaseError(f"根据实体获取属性失败: {e}")
    
    async def get_by_key(self, entity_id: int, key: str):
        """根据键获取属性"""
        try:
            from .models import Attribute
            stmt = select(Attribute).where(
                and_(Attribute.entity_id == entity_id, Attribute.key == key)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"根据键获取属性失败: {e}")
            raise DatabaseError(f"根据键获取属性失败: {e}")
    
    async def upsert(self, entity_id: int, key: str, value: str):
        """插入或更新属性 - 支持属性动态更新"""
        try:
            existing = await self.get_by_key(entity_id, key)
            if existing:
                existing.value = value
                await self.session.flush()
                await self.session.refresh(existing)
                return existing
            else:
                return await self.create(entity_id=entity_id, key=key, value=value)
        except SQLAlchemyError as e:
            logger.error(f"属性upsert失败: {e}")
            raise DatabaseError(f"属性upsert失败: {e}")
    
    async def bulk_upsert(self, entity_id: int, attributes: dict):
        """批量插入或更新属性 - 高效属性管理"""
        try:
            results = []
            for key, value in attributes.items():
                attr = await self.upsert(entity_id, key, str(value))
                results.append(attr)
            return results
        except SQLAlchemyError as e:
            logger.error(f"批量属性upsert失败: {e}")
            raise DatabaseError(f"批量属性upsert失败: {e}")
    
    async def delete_by_entity(self, entity_id: int) -> int:
        """删除实体的所有属性 - 级联删除支持"""
        try:
            from .models import Attribute
            stmt = select(Attribute).where(Attribute.entity_id == entity_id)
            result = await self.session.execute(stmt)
            attributes = result.scalars().all()
            
            count = 0
            for attr in attributes:
                await self.session.delete(attr)
                count += 1
            
            logger.info(f"删除实体属性成功: entity_id={entity_id}, count={count}")
            return count
        except SQLAlchemyError as e:
            logger.error(f"删除实体属性失败: {e}")
            raise DatabaseError(f"删除实体属性失败: {e}")


class NewsEventRepository(BaseRepository):
    """新闻事件存储库 - 包含具体的新闻事件操作逻辑"""
    
    def __init__(self, session: AsyncSession):
        # 延迟导入模型
        from .models import NewsEvent
        super().__init__(NewsEvent, session)
    
    async def get_by_title(self, title: str):
        """根据标题获取新闻事件"""
        try:
            from .models import NewsEvent
            stmt = select(NewsEvent).where(NewsEvent.title == title)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"根据标题获取新闻事件失败: {e}")
            raise DatabaseError(f"根据标题获取新闻事件失败: {e}")
    
    async def get_by_source(self, source: str, skip: int = 0, limit: int = 100):
        """根据来源获取新闻事件"""
        try:
            from .models import NewsEvent
            stmt = select(NewsEvent).where(NewsEvent.source == source).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"根据来源获取新闻事件失败: {e}")
            raise DatabaseError(f"根据来源获取新闻事件失败: {e}")
    
    async def get_by_entity(self, entity_id: int, skip: int = 0, limit: int = 100):
        """根据实体获取相关新闻事件 - 多表关联查询"""
        try:
            from .models import Entity, NewsEvent
            stmt = select(NewsEvent).join(NewsEvent.entities).where(Entity.id == entity_id).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"根据实体获取新闻事件失败: {e}")
            raise DatabaseError(f"根据实体获取新闻事件失败: {e}")
    
    async def add_entity_relation(self, news_event_id: int, entity_id: int) -> bool:
        """添加新闻事件与实体的关联 - 知识图谱构建"""
        try:
            from .models import news_event_entity
            stmt = select(news_event_entity).where(
                and_(news_event_entity.c.news_event_id == news_event_id,
                     news_event_entity.c.entity_id == entity_id)
            )
            result = await self.session.execute(stmt)
            if result.first():
                logger.warning(f"新闻事件与实体关联已存在: news_event_id={news_event_id}, entity_id={entity_id}")
                return True
            
            insert_stmt = news_event_entity.insert().values(
                news_event_id=news_event_id,
                entity_id=entity_id
            )
            await self.session.execute(insert_stmt)
            logger.info(f"新闻事件与实体关联成功: news_event_id={news_event_id}, entity_id={entity_id}")
            return True
        except IntegrityError:
            logger.warning(f"新闻事件与实体关联已存在: news_event_id={news_event_id}, entity_id={entity_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"添加新闻事件与实体关联失败: {e}")
            raise DatabaseError(f"添加新闻事件与实体关联失败: {e}")
    
    async def remove_entity_relation(self, news_event_id: int, entity_id: int) -> bool:
        """移除新闻事件与实体的关联"""
        try:
            from .models import news_event_entity
            delete_stmt = news_event_entity.delete().where(
                and_(news_event_entity.c.news_event_id == news_event_id,
                     news_event_entity.c.entity_id == entity_id)
            )
            result = await self.session.execute(delete_stmt)
            if result.rowcount > 0:
                logger.info(f"移除新闻事件与实体关联成功: news_event_id={news_event_id}, entity_id={entity_id}")
                return True
            else:
                logger.warning(f"新闻事件与实体关联不存在: news_event_id={news_event_id}, entity_id={entity_id}")
                return False
        except SQLAlchemyError as e:
            logger.error(f"移除新闻事件与实体关联失败: {e}")
            raise DatabaseError(f"移除新闻事件与实体关联失败: {e}")
    
    async def get_recent_events(self, days: int = 7, limit: int = 100):
        """获取最近的新闻事件 - 时间序列分析"""
        try:
            from .models import NewsEvent
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            stmt = select(NewsEvent).where(NewsEvent.publish_time >= cutoff_date).order_by(
                NewsEvent.publish_time.desc()).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"获取最近新闻事件失败: {e}")
            raise DatabaseError(f"获取最近新闻事件失败: {e}")
    
    async def search_by_content(self, keyword: str, limit: int = 100):
        """根据内容关键词搜索新闻事件 - 全文搜索"""
        try:
            from .models import NewsEvent
            # 简单的LIKE搜索，实际项目中可以考虑使用全文搜索引擎
            stmt = select(NewsEvent).where(
                NewsEvent.content.contains(keyword)
            ).order_by(NewsEvent.publish_time.desc()).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"搜索新闻事件失败: {e}")
            raise DatabaseError(f"搜索新闻事件失败: {e}")