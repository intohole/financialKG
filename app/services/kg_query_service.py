"""
知识图谱查询服务 - 前端友好的数据API
提供知识图谱数据查询功能，专为前端展示优化设计
"""

from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Entity, Relation, Attribute, NewsEvent, news_event_entity
from app.database.repositories import EntityRepository, RelationRepository, NewsEventRepository
from app.utils.logging_utils import get_logger
from app.services.news_search_service import NewsSearchService

logger = get_logger(__name__)


class KGQueryService:
    """
    知识图谱查询服务
    
    专为前端展示设计的数据查询服务，提供：
    - 实体和关系的分页查询
    - 实体深度遍历和关联分析
    - 实体-新闻关联查询
    - 多实体共同新闻分析
    - 新闻相关实体推荐
    
    所有查询方法都返回前端友好的数据结构，支持分页、过滤和排序
    """
    
    def __init__(self, session):
        """初始化查询服务"""
        self.session = session
        self.entity_repo = EntityRepository(session)
        self.relation_repo = RelationRepository(session)
        self.news_repo = NewsEventRepository(session)
        self.news_search_service = NewsSearchService(session)
    
    # ==================== 实体查询功能 ====================
    
    async def get_entity_list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        entity_type: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        获取实体列表 - 支持分页、搜索和过滤
        
        Args:
            page: 页码，从1开始
            page_size: 每页数量
            search: 搜索关键词（匹配名称和描述）
            entity_type: 实体类型过滤
            sort_by: 排序字段
            sort_order: 排序方向 (asc/desc)
            
        Returns:
            {
                "items": List[实体数据],
                "total": 总数量,
                "page": 当前页码,
                "page_size": 每页数量,
                "total_pages": 总页数
            }
        """
        try:
            # 构建基础查询
            stmt = select(Entity)
            
            # 应用过滤条件
            conditions = []
            if search:
                conditions.append(
                    or_(
                        Entity.name.ilike(f"%{search}%"),
                        Entity.description.ilike(f"%{search}%")
                    )
                )
            if entity_type:
                conditions.append(Entity.type == entity_type)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # 应用排序
            order_field = getattr(Entity, sort_by, Entity.created_at)
            if sort_order == "desc":
                stmt = stmt.order_by(order_field.desc())
            else:
                stmt = stmt.order_by(order_field)
            
            # 计算总数
            count_stmt = select(func.count(Entity.id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            
            total_result = await self.session.execute(count_stmt)
            total = total_result.scalar()
            
            # 分页查询
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)
            
            result = await self.session.execute(stmt)
            entities = result.scalars().all()
            
            # 转换为前端友好的格式
            items = []
            for entity in entities:
                items.append({
                    "id": entity.id,
                    "name": entity.name,
                    "entity_type": entity.type,
                    "description": entity.description,
                    "created_at": entity.created_at.isoformat() if entity.created_at else None,
                    "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
                    "confidence": getattr(entity, 'confidence', None),
                    "source_text": getattr(entity, 'source_text', '')[:200] + "..." if getattr(entity, 'source_text', None) and len(getattr(entity, 'source_text', '')) > 200 else getattr(entity, 'source_text', '')
                })
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"获取实体列表失败: {e}")
            raise
    
    async def get_entity_detail(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """
        获取实体详细信息 - 包含关联数据
        
        Args:
            entity_id: 实体ID
            
        Returns:
            实体详细信息，包含关联统计
        """
        try:
            # 获取实体基本信息
            entity = await self.entity_repo.get_by_id(entity_id)
            if not entity:
                return None
            
            # 获取关联统计
            relations_count = await self._get_entity_relations_count(entity_id)
            news_count = await self._get_entity_news_count(entity_id)
            attributes_count = await self._get_entity_attributes_count(entity_id)
            
            return {
                "id": entity.id,
                "name": entity.name,
                "entity_type": entity.type,
                "description": entity.description,
                "created_at": entity.created_at.isoformat() if entity.created_at else None,
                "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
                "confidence": getattr(entity, 'confidence', None),
                "source_text": getattr(entity, 'source_text', None),
                "metadata": getattr(entity, 'meta_data', None),
                "statistics": {
                    "relations_count": relations_count,
                    "news_count": news_count,
                    "attributes_count": attributes_count
                }
            }
            
        except Exception as e:
            logger.error(f"获取实体详情失败: {e}")
            raise
    
    # ==================== 关系查询功能 ====================
    
    async def get_relation_list(
        self,
        page: int = 1,
        page_size: int = 20,
        entity_id: Optional[int] = None,
        relation_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取关系列表 - 支持按实体和关系类型过滤
        
        Args:
            page: 页码
            page_size: 每页数量
            entity_id: 实体ID过滤（获取该实体的所有关系）
            relation_type: 关系类型过滤
            search: 搜索关键词（匹配关系类型和描述）
            
        Returns:
            分页的关系数据，包含源实体和目标实体信息
        """
        try:
            # 构建查询，关联实体表获取名称
            source_entity = Entity.__table__.alias('source_entity')
            target_entity = Entity.__table__.alias('target_entity')
            
            stmt = select(
                Relation,
                source_entity.c.name.label("source_name"),
                source_entity.c.type.label("source_type"),
                target_entity.c.name.label("target_name"),
                target_entity.c.type.label("target_type")
            ).join(
                source_entity, Relation.subject_id == source_entity.c.id
            ).join(
                target_entity, Relation.object_id == target_entity.c.id
            )
            
            # 应用过滤条件
            conditions = []
            if entity_id:
                conditions.append(
                    or_(
                        Relation.subject_id == entity_id,
                        Relation.object_id == entity_id
                    )
                )
            if relation_type:
                conditions.append(Relation.predicate == relation_type)
            if search:
                conditions.append(
                    or_(
                        Relation.predicate.ilike(f"%{search}%"),
                        Relation.description.ilike(f"%{search}%")
                    )
                )
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # 计算总数
            count_stmt = select(func.count(Relation.id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            
            total_result = await self.session.execute(count_stmt)
            total = total_result.scalar()
            
            # 分页查询
            offset = (page - 1) * page_size
            stmt = stmt.order_by(Relation.created_at.desc()).offset(offset).limit(page_size)
            
            result = await self.session.execute(stmt)
            rows = result.all()
            
            items = []
            for row in rows:
                relation, source_name, source_type, target_name, target_type = row
                items.append({
                    "id": relation.id,
                    "relation_type": relation.predicate,
                    "description": relation.description,
                    "confidence": getattr(relation, 'confidence', None),
                    "created_at": relation.created_at.isoformat() if relation.created_at else None,
                    "source_entity": {
                        "id": relation.subject_id,
                        "name": source_name,
                        "type": source_type
                    },
                    "target_entity": {
                        "id": relation.object_id,
                        "name": target_name,
                        "type": target_type
                    }
                })
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"获取关系列表失败: {e}")
            raise
    
    # ==================== 实体深度遍历功能 ====================
    
    async def get_entity_neighbors(
        self,
        entity_id: int,
        depth: int = 2,
        relation_types: Optional[List[str]] = None,
        max_entities: int = 100
    ) -> Dict[str, Any]:
        """
        获取实体的邻居网络 - 深度遍历
        
        Args:
            entity_id: 起始实体ID
            depth: 遍历深度（默认2层）
            relation_types: 关系类型过滤
            max_entities: 最大实体数量限制
            
        Returns:
            {
                "nodes": List[实体节点],
                "edges": List[关系边],
                "metadata": 遍历统计信息
            }
        """
        try:
            visited_entities = set()
            visited_relations = set()
            nodes = []
            edges = []
            
            # 获取起始实体
            start_entity = await self.entity_repo.get_by_id(entity_id)
            if not start_entity:
                return {"nodes": [], "edges": [], "metadata": {"total_nodes": 0, "total_edges": 0}}
            
            # 广度优先搜索
            current_level = [entity_id]
            visited_entities.add(entity_id)
            
            for level in range(depth):
                if len(visited_entities) >= max_entities:
                    break
                    
                next_level = []
                
                for current_entity_id in current_level:
                    # 获取当前实体的直接关系
                    relations = await self._get_entity_direct_relations(
                        current_entity_id, relation_types
                    )
                    
                    for relation in relations:
                        # 确定邻居实体ID
                        if relation.subject_id == current_entity_id:
                            neighbor_id = relation.object_id
                        else:
                            neighbor_id = relation.subject_id
                        
                        # 如果邻居实体未访问过，添加到下一层
                        if neighbor_id not in visited_entities and len(visited_entities) < max_entities:
                            visited_entities.add(neighbor_id)
                            next_level.append(neighbor_id)
                        
                        # 添加关系边（如果未添加过）
                        if relation.id not in visited_relations:
                            visited_relations.add(relation.id)
                            edges.append({
                                "id": relation.id,
                                "source": relation.subject_id,
                                "target": relation.object_id,
                                "relation_type": relation.predicate,
                                "description": relation.description,
                                "confidence": getattr(relation, 'confidence', None)
                            })
                
                current_level = next_level
            
            # 获取所有访问过的实体详细信息
            if visited_entities:
                entities_stmt = select(Entity).where(Entity.id.in_(list(visited_entities)))
                entities_result = await self.session.execute(entities_stmt)
                entities = entities_result.scalars().all()
                
                for entity in entities:
                    nodes.append({
                        "id": entity.id,
                        "name": entity.name,
                        "entity_type": entity.type,
                        "description": entity.description,
                        "confidence": getattr(entity, 'confidence', None),
                        "is_center": entity.id == entity_id  # 标记中心节点
                    })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "center_entity_id": entity_id,
                    "max_depth": depth,
                    "visited_at_depth": len(visited_entities)
                }
            }
            
        except Exception as e:
            logger.error(f"获取实体邻居网络失败: {e}")
            raise
    
    # ==================== 实体-新闻关联查询功能 ====================
    
    async def get_entity_news(
        self,
        entity_id: int,
        page: int = 1,
        page_size: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取实体关联的新闻
        
        Args:
            entity_id: 实体ID
            page: 页码
            page_size: 每页数量
            start_date: 开始日期过滤
            end_date: 结束日期过滤
            
        Returns:
            分页的新闻数据
        """
        try:
            # 通过关联表查询新闻
            stmt = select(NewsEvent).join(
                news_event_entity, NewsEvent.id == news_event_entity.c.news_event_id
            ).where(news_event_entity.c.entity_id == entity_id)
            
            # 应用日期过滤
            if start_date:
                stmt = stmt.where(NewsEvent.publish_time >= start_date)
            if end_date:
                stmt = stmt.where(NewsEvent.publish_time <= end_date)
            
            # 计算总数
            count_stmt = select(func.count(NewsEvent.id)).join(
                news_event_entity, NewsEvent.id == news_event_entity.c.news_event_id
            ).where(news_event_entity.c.entity_id == entity_id)
            
            if start_date:
                count_stmt = count_stmt.where(NewsEvent.publish_time >= start_date)
            if end_date:
                count_stmt = count_stmt.where(NewsEvent.publish_time <= end_date)
            
            total_result = await self.session.execute(count_stmt)
            total = total_result.scalar()
            
            # 分页查询
            offset = (page - 1) * page_size
            stmt = stmt.order_by(NewsEvent.publish_time.desc()).offset(offset).limit(page_size)
            
            result = await self.session.execute(stmt)
            news_list = result.scalars().all()
            
            items = []
            for news in news_list:
                items.append({
                    "id": getattr(news, 'id', None),
                    "title": getattr(news, 'title', None),
                    "content": (getattr(news, 'content', '')[:300] + "..." if len(getattr(news, 'content', '')) > 300 else getattr(news, 'content', '')),
                    "source": getattr(news, 'source', None),
                    "published_at": news.publish_time.isoformat() if news.publish_time else None,
                    "created_at": news.created_at.isoformat() if news.created_at else None,
                    "updated_at": news.updated_at.isoformat() if news.updated_at else None
                })
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"获取实体关联新闻失败: {e}")
            raise
    
    # ==================== 多实体共同新闻查询功能 ====================
    
    async def get_common_news_for_entities(
        self,
        entity_ids: List[int],
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        获取多个实体共同关联的新闻
        
        Args:
            entity_ids: 实体ID列表
            page: 页码
            page_size: 每页数量
            
        Returns:
            共同关联的新闻数据
        """
        try:
            if len(entity_ids) < 2:
                return {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "entity_count": len(entity_ids)
                }
            
            # 构建查询：新闻必须关联所有指定实体
            # 使用子查询确保新闻关联了所有实体
            subqueries = []
            for entity_id in entity_ids:
                subquery = select(news_event_entity.c.news_event_id).where(
                    news_event_entity.c.entity_id == entity_id
                )
                subqueries.append(subquery)
            
            # 获取所有实体都关联的新闻ID
            if subqueries:
                # 使用INTERSECT获取交集
                intersect_query = subqueries[0]
                for subquery in subqueries[1:]:
                    intersect_query = intersect_query.intersect(subquery)
                
                # 主查询
                stmt = select(NewsEvent).where(NewsEvent.id.in_(intersect_query))
                
                # 计算总数
                count_stmt = select(func.count(NewsEvent.id)).where(NewsEvent.id.in_(intersect_query))
                total_result = await self.session.execute(count_stmt)
                total = total_result.scalar()
                
                # 分页查询
                offset = (page - 1) * page_size
                stmt = stmt.order_by(NewsEvent.publish_time.desc()).offset(offset).limit(page_size)
                
                result = await self.session.execute(stmt)
                news_list = result.scalars().all()
                
                items = []
                for news in news_list:
                    items.append({
                        "id": getattr(news, 'id', None),
                        "title": getattr(news, 'title', None),
                        "content": (getattr(news, 'content', '')[:300] + "..." if len(getattr(news, 'content', '')) > 300 else getattr(news, 'content', '')),
                        "source": getattr(news, 'source', None),
                        "published_at": news.publish_time.isoformat() if news.publish_time else None,
                        "created_at": news.created_at.isoformat() if news.created_at else None,
                        "updated_at": news.updated_at.isoformat() if news.updated_at else None
                    })
                
                return {
                    "items": items,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size,
                    "entity_count": len(entity_ids)
                }
            
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "entity_count": len(entity_ids)
            }
            
        except Exception as e:
            logger.error(f"获取多实体共同新闻失败: {e}")
            raise
    
    # ==================== 新闻相关实体查询功能 ====================
    
    async def get_news_entities(
        self,
        news_id: int,
        entity_type: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        获取新闻相关的实体
        
        Args:
            news_id: 新闻ID
            entity_type: 实体类型过滤
            limit: 返回实体数量限制
            
        Returns:
            相关实体数据，按重要性排序
        """
        try:
            # 通过关联表查询实体
            stmt = select(Entity).join(
                news_event_entity, Entity.id == news_event_entity.c.entity_id
            ).where(news_event_entity.c.news_event_id == news_id)
            
            # 应用实体类型过滤
            if entity_type:
                stmt = stmt.where(Entity.type == entity_type)
            
            # 按置信度排序，限制数量
            stmt = stmt.order_by(Entity.confidence.desc()).limit(limit)
            
            result = await self.session.execute(stmt)
            entities = result.scalars().all()
            
            # 获取实体统计信息
            entity_data = []
            for entity in entities:
                # 获取该实体在此新闻中的相关性分数（简化版本）
                relevance_score = await self._calculate_entity_news_relevance(entity.id, news_id)
                
                entity_data.append({
                    "id": entity.id,
                    "name": entity.name,
                    "entity_type": entity.type,
                    "description": entity.description,
                    "confidence": getattr(entity, 'confidence', None),
                    "relevance_score": relevance_score,
                    "created_at": entity.created_at.isoformat() if entity.created_at else None
                })
            
            # 按相关性分数重新排序
            entity_data.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return {
                "entities": entity_data,
                "total": len(entity_data),
                "news_id": news_id,
                "entity_type_filter": entity_type
            }
            
        except Exception as e:
            logger.error(f"获取新闻相关实体失败: {e}")
            raise
    
    # ==================== 辅助方法 ====================
    
    async def _get_entity_direct_relations(
        self, entity_id: int, relation_types: Optional[List[str]] = None
    ) -> List[Relation]:
        """获取实体的直接关系"""
        stmt = select(Relation).where(
            or_(Relation.subject_id == entity_id, Relation.object_id == entity_id)
        )
        
        if relation_types:
            stmt = stmt.where(Relation.predicate.in_(relation_types))
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def _get_entity_relations_count(self, entity_id: int) -> int:
        """获取实体关系数量"""
        stmt = select(func.count(Relation.id)).where(
            or_(Relation.subject_id == entity_id, Relation.object_id == entity_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def _get_entity_news_count(self, entity_id: int) -> int:
        """获取实体关联新闻数量"""
        stmt = select(func.count(news_event_entity.c.news_event_id)).where(
            news_event_entity.c.entity_id == entity_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def _get_entity_attributes_count(self, entity_id: int) -> int:
        """获取实体属性数量"""
        # 这里需要根据实际的属性表结构调整
        # 暂时返回0，后续根据实际模型实现
        return 0
    
    async def _calculate_entity_news_relevance(self, entity_id: int, news_id: int) -> float:
        """
        计算实体在新闻中的相关性分数
        简化实现：基于实体置信度和在新闻中的出现频率
        """
        try:
            # 这里可以实现更复杂的 relevance 计算逻辑
            # 暂时返回实体的置信度作为相关性分数
            entity = await self.entity_repo.get_by_id(entity_id)
            return getattr(entity, 'confidence', 0.0) if entity else 0.0
        except:
            return 0.0
    
    # ==================== 新闻列表查询功能 ====================
    
    async def get_news_list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        source: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "publish_time",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        获取新闻列表 - 支持分页、搜索和时间过滤
        
        Args:
            page: 页码，从1开始
            page_size: 每页数量
            search: 搜索关键词（匹配标题和内容）
            source: 新闻来源过滤
            start_date: 开始日期过滤
            end_date: 结束日期过滤
            sort_by: 排序字段
            sort_order: 排序方向 (asc/desc)
            
        Returns:
            {
                "items": List[新闻数据],
                "total": 总数量,
                "page": 当前页码,
                "page_size": 每页数量,
                "total_pages": 总页数
            }
        """
        try:
            # 构建基础查询
            stmt = select(NewsEvent)
            
            # 应用过滤条件
            conditions = []
            if search:
                conditions.append(
                    or_(
                        NewsEvent.title.ilike(f"%{search}%"),
                        NewsEvent.content.ilike(f"%{search}%")
                    )
                )
            if source:
                conditions.append(NewsEvent.source == source)
            if start_date:
                conditions.append(NewsEvent.publish_time >= start_date)
            if end_date:
                conditions.append(NewsEvent.publish_time <= end_date)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # 应用排序
            order_field = getattr(NewsEvent, sort_by, NewsEvent.publish_time)
            if sort_order == "desc":
                stmt = stmt.order_by(order_field.desc())
            else:
                stmt = stmt.order_by(order_field)
            
            # 计算总数
            count_stmt = select(func.count(NewsEvent.id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            
            total_result = await self.session.execute(count_stmt)
            total = total_result.scalar()
            
            # 分页查询
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)
            
            result = await self.session.execute(stmt)
            news_list = result.scalars().all()
            
            # 转换为前端友好的格式
            items = []
            for news in news_list:
                items.append({
                    "id": getattr(news, 'id', None),
                    "title": getattr(news, 'title', None),
                    "content": (getattr(news, 'content', '')[:500] + "..." if len(getattr(news, 'content', '')) > 500 else getattr(news, 'content', '')),
                    "summary": getattr(news, 'summary', None),
                    "url": getattr(news, 'url', None),
                    "source": getattr(news, 'source', None),
                    "published_at": getattr(news, 'publish_time', None).isoformat() if getattr(news, 'publish_time', None) else None,
                    "sentiment": getattr(news, 'sentiment', None),
                    "category": getattr(news, 'category', None),
                    "created_at": getattr(news, 'created_at', None).isoformat() if getattr(news, 'created_at', None) else None,
                    "updated_at": getattr(news, 'updated_at', None).isoformat() if getattr(news, 'updated_at', None) else None
                })
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"获取新闻列表失败: {e}")
            raise