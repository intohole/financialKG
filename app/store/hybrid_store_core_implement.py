"""
HybridStore核心模块 - 专注基础存储能力

核心功能：
- 基础CRUD操作（实体、关系、新闻事件）
- 向量索引管理
- 事务管理
- 健康检查

设计原则：
- 单一职责：只提供基础存储能力
- 业务逻辑上移：复杂的业务逻辑由服务层处理
- 接口清晰：明确定义输入输出
- 异常处理：统一的异常处理机制
"""

import logging
from typing import List, Dict, Any, Optional

from app.database.manager import DatabaseManager
from app.database.repositories import EntityRepository, RelationRepository, NewsEventRepository
from app.store.store_base_abstract import StoreBase, Entity, Relation, NewsEvent, SearchResult, StoreConfig
from app.store.store_exceptions_define import StoreError, EntityNotFoundError, RelationNotFoundError
from app.store.store_data_convert import DataConverter
from app.store.vector_index_manage import VectorIndexManager
from app.vector.base import VectorSearchBase
from app.embedding import EmbeddingService


logger = logging.getLogger(__name__)


class HybridStoreCore(StoreBase):
    """HybridStore核心类 - 提供基础存储能力
    
    核心能力：
    1. 实体CRUD：创建、读取、更新、删除实体
    2. 关系CRUD：创建、读取、更新、删除关系
    3. 新闻事件CRUD：创建、读取、更新、删除新闻事件
    4. 向量操作：添加、搜索向量
    5. 事务管理：开始、提交、回滚事务
    6. 健康检查：检查存储系统状态
    
    非职责：
    - 复杂的业务逻辑（如实体合并策略）
    - 智能推荐算法
    - 知识图谱分析
    """
    
    def __init__(self, db_manager: DatabaseManager, vector_store: VectorSearchBase, 
                 embedding_service: EmbeddingService) -> None:
        """初始化HybridStore核心
        
        Args:
            db_manager: 数据库管理器
            vector_store: 向量存储实例
            embedding_service: 嵌入服务
        """
        self.db_manager = db_manager
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        
        # 初始化工具
        self.vector_manager = VectorIndexManager(vector_store, embedding_service)
        self.data_converter = DataConverter()
        
        self._initialized = False
    
    async def initialize(self, config: Optional[StoreConfig] = None) -> None:
        """初始化存储
        
        Args:
            config: 存储配置，可选
            
        Raises:
            StoreError: 初始化失败时抛出
        """
        if self._initialized:
            return
        
        try:
            # 初始化数据库管理器 - 创建数据表
            await self.db_manager.create_tables()
            
            # 初始化向量索引管理器
            await self.vector_manager.initialize()
            
            self._initialized = True
            logger.info("HybridStore核心初始化成功")
            
        except Exception as e:
            logger.error(f"HybridStore核心初始化失败: {e}")
            raise StoreError(f"HybridStore核心初始化失败: {str(e)}")
    
    async def close(self) -> None:
        """关闭存储
        
        Raises:
            StoreError: 关闭失败时抛出
        """
        if not self._initialized:
            return
        
        try:
            # 关闭数据库连接
            await self.db_manager.close()
            
            # 关闭向量存储 - close 是同步方法
            if hasattr(self, 'vector_store') and self.vector_store:
                self.vector_store.close()
            
            self._initialized = False
            logger.info("HybridStore核心关闭成功")
            
        except Exception as e:
            logger.error(f"HybridStore核心关闭失败: {e}")
            raise StoreError(f"HybridStore核心关闭失败: {str(e)}")
    
    # 实体操作
    async def create_entity(self, entity: Entity) -> Entity:
        """创建实体
        
        Args:
            entity: 要创建的实体对象
            
        Returns:
            Entity: 创建后的实体对象，包含分配的ID和向量ID
            
        Raises:
            StoreError: 创建失败时抛出
        """
        try:
            async with self.db_manager.get_session() as session:
                # 创建数据库实体
                entity_repository = EntityRepository(session)
                db_entity_data = self.data_converter.entity_to_db_entity(entity)
                created_entity = await entity_repository.create(db_entity_data)
                
                # 添加到向量索引
                content = f"{entity.name}: {entity.description}"
                metadata = {
                    "type": entity.type,
                    "name": entity.name,
                    "description": entity.description
                }
                
                vector_id = await self.vector_manager.add_to_index(
                    content, created_entity.id, "entity", metadata
                )
                
                # 更新实体的vector_id字段
                created_entity.vector_id = vector_id
                await session.flush()
                
                # 转换回业务实体
                return self.data_converter.db_entity_to_entity(created_entity, vector_id)
                
        except Exception as e:
            logger.error(f"创建实体失败: {e}")
            raise StoreError(f"创建实体失败: {str(e)}")
    
    async def get_entity(self, entity_id: int) -> Optional[Entity]:
        """获取实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            Optional[Entity]: 实体对象，如果未找到则返回None
            
        Raises:
            StoreError: 获取失败时抛出
        """
        try:
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                db_entity = await entity_repository.get_by_id(entity_id)
                if not db_entity:
                    return None
                
                # 从数据库实体获取vector_id
                vector_id = getattr(db_entity, 'vector_id', None)
                return self.data_converter.db_entity_to_entity(db_entity, vector_id)
                
        except Exception as e:
            logger.error(f"获取实体失败: {e}")
            raise StoreError(f"获取实体失败: {str(e)}")
    
    async def update_entity(self, entity_id: int, updates: Dict[str, Any]) -> Entity:
        """更新实体
        
        Args:
            entity_id: 实体ID
            updates: 更新数据
            
        Returns:
            Entity: 更新后的实体
            
        Raises:
            EntityNotFoundError: 实体未找到
            StoreError: 更新失败
        """
        try:
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                
                # 检查实体是否存在
                existing_entity = await entity_repository.get_by_id(entity_id)
                if not existing_entity:
                    raise EntityNotFoundError(f"实体未找到: {entity_id}")
                
                # 更新实体
                updated_entity = await entity_repository.update(entity_id, updates)
                
                # 如果更新了名称或描述，需要更新向量索引
                if 'name' in updates or 'description' in updates:
                    content = f"{updated_entity.name}: {updated_entity.description}"
                    metadata = {
                        "type": updated_entity.type,
                        "name": updated_entity.name,
                        "description": updated_entity.description
                    }
                    
                    if hasattr(updated_entity, 'vector_id') and updated_entity.vector_id:
                        await self.vector_manager.update_vector(
                            updated_entity.vector_id, content, metadata
                        )
                
                vector_id = getattr(updated_entity, 'vector_id', None)
                return self.data_converter.db_entity_to_entity(updated_entity, vector_id)
                
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"更新实体失败: {e}")
            raise StoreError(f"更新实体失败: {str(e)}")
    
    async def delete_entity(self, entity_id: int) -> bool:
        """删除实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            bool: 是否成功删除
            
        Raises:
            EntityNotFoundError: 实体未找到
            StoreError: 删除失败
        """
        try:
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                
                # 检查实体是否存在
                existing_entity = await entity_repository.get_by_id(entity_id)
                if not existing_entity:
                    raise EntityNotFoundError(f"实体未找到: {entity_id}")
                
                # 删除向量索引
                if hasattr(existing_entity, 'vector_id') and existing_entity.vector_id:
                    await self.vector_manager.delete_vector(existing_entity.vector_id)
                
                # 删除实体
                success = await entity_repository.delete(entity_id)
                return success
                
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"删除实体失败: {e}")
            raise StoreError(f"删除实体失败: {str(e)}")
    
    async def search_entities(self, 
                            query: str, 
                            entity_type: Optional[str] = None,
                            top_k: int = 10,
                            include_vector_search: bool = True,
                            include_full_text_search: bool = False) -> List[SearchResult]:
        """搜索实体 - 仅使用向量搜索，提高搜索效率
        
        Args:
            query: 搜索查询
            entity_type: 实体类型过滤
            top_k: 返回结果数量
            include_vector_search: 是否包含向量搜索（默认启用）
            include_full_text_search: 是否包含全文搜索（默认禁用，仅使用向量搜索）
            
        Returns:
            List[SearchResult]: 搜索结果列表
            
        Raises:
            StoreError: 搜索失败
        """
        try:
            results = []
            
            # 仅使用向量搜索，提高搜索效率
            if include_vector_search:
                # 添加实体类型过滤到查询中
                search_query = query
                if entity_type:
                    search_query = f"{query} type:{entity_type}"
                    
                vector_results = await self.vector_manager.search_vectors(
                    search_query, "entity", top_k, 
                    {"type": entity_type} if entity_type else None
                )
                
                for vector_result in vector_results:
                    entity_id = vector_result.get('metadata', {}).get('content_id')
                    if entity_id:
                        entity = await self.get_entity(int(entity_id))
                        if entity:
                            results.append(SearchResult(
                                entity=entity,
                                score=vector_result.get('score', 0.0),
                                metadata=vector_result.get('metadata', {})
                            ))
            
            # 按分数排序并限制数量
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"搜索实体失败: {e}")
            raise StoreError(f"搜索实体失败: {str(e)}")
    
    # 关系操作
    async def create_relation(self, relation: Relation) -> Relation:
        """创建关系
        
        Args:
            relation: 要创建的关系对象
            
        Returns:
            Relation: 创建后的关系对象
            
        Raises:
            StoreError: 创建失败
        """
        try:
            async with self.db_manager.get_session() as session:
                relation_repository = RelationRepository(session)
                db_relation_data = self.data_converter.relation_to_db_relation(relation)
                created_relation = await relation_repository.create(db_relation_data)
                
                return self.data_converter.db_relation_to_relation(created_relation)
                
        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            raise StoreError(f"创建关系失败: {str(e)}")
    
    async def get_relation(self, relation_id: int) -> Optional[Relation]:
        """获取关系
        
        Args:
            relation_id: 关系ID
            
        Returns:
            Optional[Relation]: 关系对象，如果未找到则返回None
            
        Raises:
            StoreError: 获取失败
        """
        try:
            async with self.db_manager.get_session() as session:
                relation_repository = RelationRepository(session)
                db_relation = await relation_repository.get_by_id(relation_id)
                if not db_relation:
                    return None
                
                return self.data_converter.db_relation_to_relation(db_relation)
                
        except Exception as e:
            logger.error(f"获取关系失败: {e}")
            raise StoreError(f"获取关系失败: {str(e)}")
    
    async def get_entity_relations(self, entity_id: int, 
                                 predicate: Optional[str] = None) -> List[Relation]:
        """获取实体的所有关系
        
        Args:
            entity_id: 实体ID
            predicate: 关系谓词过滤
            
        Returns:
            List[Relation]: 关系列表
            
        Raises:
            StoreError: 获取失败
        """
        try:
            async with self.db_manager.get_session() as session:
                relation_repository = RelationRepository(session)
                db_relations = await relation_repository.get_entity_relations(entity_id, predicate)
                
                return [self.data_converter.db_relation_to_relation(r) for r in db_relations]
                
        except Exception as e:
            logger.error(f"获取实体关系失败: {e}")
            raise StoreError(f"获取实体关系失败: {str(e)}")
    
    async def delete_relation(self, relation_id: int) -> bool:
        """删除关系
        
        Args:
            relation_id: 关系ID
            
        Returns:
            bool: 是否成功删除
            
        Raises:
            RelationNotFoundError: 关系未找到
            StoreError: 删除失败
        """
        try:
            async with self.db_manager.get_session() as session:
                relation_repository = RelationRepository(session)
                
                # 检查关系是否存在
                existing_relation = await relation_repository.get_by_id(relation_id)
                if not existing_relation:
                    raise RelationNotFoundError(f"关系未找到: {relation_id}")
                
                # 删除关系
                success = await relation_repository.delete(relation_id)
                return success
                
        except RelationNotFoundError:
            raise
        except Exception as e:
            logger.error(f"删除关系失败: {e}")
            raise StoreError(f"删除关系失败: {str(e)}")
    
    # 新闻事件操作
    async def create_news_event(self, news_event: NewsEvent) -> NewsEvent:
        """创建新闻事件
        
        Args:
            news_event: 新闻事件对象
            
        Returns:
            NewsEvent: 创建后的新闻事件
            
        Raises:
            StoreError: 创建失败
        """
        try:
            async with self.db_manager.get_session() as session:
                news_repository = NewsEventRepository(session)
                db_news_data = self.data_converter.news_event_to_db_news_event(news_event)
                created_news = await news_repository.create(db_news_data)
                
                # 添加到向量索引
                content = f"{news_event.title}: {news_event.content}"
                metadata = {
                    "type": "news",
                    "title": news_event.title,
                    "source": news_event.source,
                    "publish_time": news_event.publish_time.isoformat() if news_event.publish_time else None
                }
                
                vector_id = await self.vector_manager.add_to_index(
                    content, created_news.id, "news", metadata
                )
                
                # 更新向量的ID字段
                created_news.vector_id = vector_id
                await session.flush()
                
                return self.data_converter.db_news_event_to_news_event(created_news, vector_id)
                
        except Exception as e:
            logger.error(f"创建新闻事件失败: {e}")
            raise StoreError(f"创建新闻事件失败: {str(e)}")
    
    async def get_news_event(self, news_event_id: int) -> Optional[NewsEvent]:
        """获取新闻事件
        
        Args:
            news_event_id: 新闻事件ID
            
        Returns:
            Optional[NewsEvent]: 新闻事件对象，如果未找到则返回None
            
        Raises:
            StoreError: 获取失败
        """
        try:
            async with self.db_manager.get_session() as session:
                news_repository = NewsEventRepository(session)
                db_news = await news_repository.get_by_id(news_event_id)
                if not db_news:
                    return None
                
                vector_id = getattr(db_news, 'vector_id', None)
                return self.data_converter.db_news_event_to_news_event(db_news, vector_id)
                
        except Exception as e:
            logger.error(f"获取新闻事件失败: {e}")
            raise StoreError(f"获取新闻事件失败: {str(e)}")
    
    async def search_news_events(self, 
                               query: str,
                               top_k: int = 10,
                               time_range: Optional[tuple] = None) -> List[SearchResult]:
        """搜索新闻事件
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            time_range: 时间范围过滤 (start_time, end_time)
            
        Returns:
            List[SearchResult]: 搜索结果列表
            
        Raises:
            StoreError: 搜索失败
        """
        try:
            # 向量搜索
            filter_dict = {}
            if time_range:
                filter_dict["publish_time"] = {
                    "$gte": time_range[0].isoformat(),
                    "$lte": time_range[1].isoformat()
                }
            
            vector_results = await self.vector_manager.search_vectors(
                query, "news", top_k, filter_dict
            )
            
            results = []
            for vector_result in vector_results:
                news_id = vector_result.get('metadata', {}).get('content_id')
                if news_id:
                    news_event = await self.get_news_event(int(news_id))
                    if news_event:
                        results.append(SearchResult(
                            news_event=news_event,
                            score=vector_result.get('score', 0.0),
                            metadata=vector_result.get('metadata', {})
                        ))
            
            return results
            
        except Exception as e:
            logger.error(f"搜索新闻事件失败: {e}")
            raise StoreError(f"搜索新闻事件失败: {str(e)}")
    
    # 向量操作
    async def add_to_vector_index(self, 
                                content: str,
                                content_id: str,
                                content_type: str,
                                metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加到向量索引
        
        Args:
            content: 内容文本
            content_id: 内容ID
            content_type: 内容类型（entity, relation, news）
            metadata: 元数据
            
        Returns:
            str: 向量ID
            
        Raises:
            StoreError: 添加失败
        """
        try:
            return await self.vector_manager.add_to_index(
                content, content_id, content_type, metadata
            )
        except Exception as e:
            logger.error(f"添加到向量索引失败: {e}")
            raise StoreError(f"添加到向量索引失败: {str(e)}")
    
    async def search_vectors(self, 
                           query: str,
                           content_type: Optional[str] = None,
                           top_k: int = 10,
                           filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """向量搜索
        
        Args:
            query: 搜索查询
            content_type: 内容类型过滤
            top_k: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            List[SearchResult]: 搜索结果列表
            
        Raises:
            StoreError: 搜索失败
        """
        try:
            vector_results = await self.vector_manager.search_vectors(
                query, content_type, top_k, filter_dict
            )
            
            results = []
            for vector_result in vector_results:
                results.append(SearchResult(
                    score=vector_result.get('score', 0.0),
                    metadata=vector_result.get('metadata', {})
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise StoreError(f"向量搜索失败: {str(e)}")
    
    # 事务操作
    async def begin_transaction(self) -> None:
        """开始事务
        
        Raises:
            StoreError: 开始事务失败
        """
        try:
            await self.db_manager.begin_transaction()
        except Exception as e:
            logger.error(f"开始事务失败: {e}")
            raise StoreError(f"开始事务失败: {str(e)}")
    
    async def commit_transaction(self) -> None:
        """提交事务
        
        Raises:
            StoreError: 提交事务失败
        """
        try:
            await self.db_manager.commit_transaction()
        except Exception as e:
            logger.error(f"提交事务失败: {e}")
            raise StoreError(f"提交事务失败: {str(e)}")
    
    async def rollback_transaction(self) -> None:
        """回滚事务
        
        Raises:
            StoreError: 回滚事务失败
        """
        try:
            await self.db_manager.rollback_transaction()
        except Exception as e:
            logger.error(f"回滚事务失败: {e}")
            raise StoreError(f"回滚事务失败: {str(e)}")
    
    # 健康检查
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
            
        Raises:
            StoreError: 检查失败
        """
        try:
            status = {
                "status": "healthy",
                "database": "unknown",
                "vector_store": "unknown",
                "initialized": self._initialized
            }
            
            # 检查数据库
            try:
                async with self.db_manager.get_session() as session:
                    await session.execute("SELECT 1")
                    status["database"] = "healthy"
            except Exception as e:
                status["database"] = f"unhealthy: {str(e)}"
                status["status"] = "unhealthy"
            
            # 检查向量存储
            try:
                if self.vector_store:
                    await self.vector_store.health_check()
                    status["vector_store"] = "healthy"
            except Exception as e:
                status["vector_store"] = f"unhealthy: {str(e)}"
                status["status"] = "unhealthy"
            
            return status
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            raise StoreError(f"健康检查失败: {str(e)}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()