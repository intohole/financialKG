"""
HybridStore核心模块
包含HybridStore主类和核心逻辑
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from app.database.manager import DatabaseManager
from app.database.repositories import EntityRepository, RelationRepository, NewsEventRepository
from app.store.base import StoreBase, Entity, Relation, NewsEvent, StoreConfig, SearchResult
from app.store.exceptions import StoreError, EntityNotFoundError, RelationNotFoundError
from app.store.data_converter import DataConverter
from app.store.vector_index_manager import VectorIndexManager
from app.store.entity_operations import EntityOperations
from app.store.relation_operations import RelationOperations
from app.vector.base import VectorSearchBase
from app.embedding import EmbeddingService


logger = logging.getLogger(__name__)


class HybridStoreCore(StoreBase):
    """HybridStore核心类 - 整合Chroma向量数据库和SQLAlchemy关系型数据库"""
    
    def __init__(self, db_manager: DatabaseManager, vector_store: VectorSearchBase, 
                 embedding_service: EmbeddingService, executor: ThreadPoolExecutor) -> None:
        """初始化HybridStore核心
        
        Args:
            db_manager: 数据库管理器
            vector_store: 向量存储实例
            embedding_service: 嵌入服务
            executor: 线程池执行器
        """
        self.db_manager = db_manager
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.executor = executor
        
        # 初始化工具
        self.vector_manager = VectorIndexManager(vector_store, embedding_service, executor)
        self.data_converter = DataConverter()
        
        # 初始化操作模块
        self.entity_operations = EntityOperations(db_manager, self.vector_manager, self.data_converter, executor)
        self.relation_operations = RelationOperations(db_manager, self.vector_manager, self.data_converter, executor)
        
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
            
            # 向量存储在构造函数中已经初始化，不需要额外初始化
            # 初始化向量索引管理器
            # 这里需要确保vector_manager已经通过构造函数初始化
            
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
            
            # 关闭向量存储
            if self.vector_store:
                await self.vector_store.close()
            
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
                
                logger.debug(f"准备添加实体到向量索引: entity_id={created_entity.id}, content='{content}', metadata={metadata}")
                
                vector_id = await self.vector_manager.add_to_index(
                    content, created_entity.id, "entity", metadata
                )
                
                logger.debug(f"实体向量添加完成: vector_id='{vector_id}'")
                
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
            logger.info(f"开始获取实体，ID: {entity_id}")
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                db_entity = await entity_repository.get_by_id(entity_id)
                logger.info(f"数据库查询结果: {db_entity}")
                if not db_entity:
                    logger.warning(f"实体未找到，ID: {entity_id}")
                    return None
                
                # 从数据库实体获取vector_id
                vector_id = getattr(db_entity, 'vector_id', None)
                logger.info(f"实体vector_id: {vector_id}")
                result = self.data_converter.db_entity_to_entity(db_entity, vector_id)
                logger.info(f"转换后的实体: {result}")
                return result
                
        except Exception as e:
            logger.error(f"获取实体失败: {e}")
            raise StoreError(f"获取实体失败: {str(e)}")
    
    async def update_entity(self, entity: Entity) -> Entity:
        """更新实体
        
        Args:
            entity: 要更新的实体对象，必须包含有效的ID
            
        Returns:
            Entity: 更新后的实体对象
            
        Raises:
            EntityNotFoundError: 实体未找到时抛出
            StoreError: 更新失败时抛出
        """
        try:
            async with self.db_manager.get_session() as session:
                # 获取原始实体
                entity_repository = EntityRepository(session)
                original_entity = await entity_repository.get_by_id(entity.id)
                if not original_entity:
                    raise EntityNotFoundError(f"实体未找到: {entity.id}")
                
                # 更新数据库实体
                db_entity_data = self.data_converter.entity_to_db_entity(entity)
                updated_entity = await entity_repository.update(db_entity_data)
                
                # 更新向量索引
                content = f"{entity.name}: {entity.description}"
                metadata = {
                    "type": entity.type,
                    "name": entity.name,
                    "description": entity.description
                }
                
                # 这里假设原始实体有vector_id，实际实现可能需要调整
                if hasattr(original_entity, 'vector_id') and original_entity.vector_id:
                    await self.vector_manager.update_vector(
                        original_entity.vector_id, content, metadata
                    )
                
                return self.data_converter.db_entity_to_entity(updated_entity)
                
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"更新实体失败: {e}")
            raise StoreError(f"更新实体失败: {str(e)}")
    
    async def delete_entity(self, entity_id: int) -> bool:
        """删除实体
        
        Args:
            entity_id: 要删除的实体ID
            
        Returns:
            bool: 删除成功返回True，实体不存在返回False
            
        Raises:
            StoreError: 删除失败时抛出
        """
        try:
            async with self.db_manager.get_session() as session:
                # 获取实体
                entity_repository = EntityRepository(session)
                relation_repository = RelationRepository(session)
                
                entity = await entity_repository.get_by_id(entity_id)
                if not entity:
                    return False
                
                # 删除相关关系
                relations = await entity_repository.get_entity_relations(entity_id)
                for relation in relations:
                    await relation_repository.delete(relation.id)
                    # 删除关系向量
                    if hasattr(relation, 'vector_id') and relation.vector_id:
                        await self.vector_manager.delete_vector(relation.vector_id)
                
                # 删除实体
                success = await entity_repository.delete(entity_id)
                
                # 删除实体向量
                if hasattr(entity, 'vector_id') and entity.vector_id:
                    await self.vector_manager.delete_vector(entity.vector_id)
                
                return success
                
        except Exception as e:
            logger.error(f"删除实体失败: {e}")
            raise StoreError(f"删除实体失败: {str(e)}")
    
    async def search_entities(self, query: str, entity_type: Optional[str] = None,
                             top_k: int = 10, include_vector_search: bool = True,
                             include_full_text_search: bool = True) -> List[Dict[str, Any]]:
        """搜索实体
        
        Args:
            query: 搜索查询字符串
            entity_type: 实体类型过滤，可选
            top_k: 返回结果数量限制
            include_vector_search: 是否包含向量搜索
            include_full_text_search: 是否包含全文搜索
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表，每个结果包含实体信息和相似度分数
            
        Raises:
            StoreError: 搜索失败时抛出
        """
        try:
            # 向量搜索
            results = await self.vector_manager.search_vectors(query, "entity", top_k)
            
            # 获取实体ID - 从搜索结果中提取content_id
            entity_ids = []
            for result in results:
                if result.get('metadata') and 'content_id' in result['metadata']:
                    content_id = result['metadata']['content_id']
                    try:
                        entity_ids.append(int(content_id))  # 转换为整数ID
                    except (ValueError, TypeError):
                        logger.warning(f"无效的实体ID格式: {content_id}")
                        continue
            
            # 获取实体
            entities = []
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                for entity_id in entity_ids:
                    entity = await entity_repository.get_by_id(entity_id)
                    if entity:
                        # 类型过滤
                        if not entity_type or entity.type == entity_type:
                            entities.append(self.data_converter.db_entity_to_entity(entity))
            
            return entities
            
        except Exception as e:
            logger.error(f"搜索实体失败: {e}")
            raise StoreError(f"搜索实体失败: {str(e)}")
    
    # 关系操作
    async def create_relation(self, relation: Relation) -> Relation:
        """创建关系
        
        Args:
            relation: 要创建的关系对象
            
        Returns:
            Relation: 创建后的关系对象，包含分配的ID和向量ID
            
        Raises:
            EntityNotFoundError: 关系的主体或客体实体不存在时抛出
            StoreError: 创建失败时抛出
        """
        try:
            async with self.db_manager.get_session() as session:
                # 验证实体存在
                entity_repository = EntityRepository(session)
                relation_repository = RelationRepository(session)
                
                subject = await entity_repository.get_by_id(relation.subject_id)
                obj = await entity_repository.get_by_id(relation.object_id)
                if not subject or not obj:
                    raise EntityNotFoundError("关系的主体或客体不存在")
                
                # 创建数据库关系
                db_relation_data = self.data_converter.relation_to_db_relation(relation)
                created_relation = await relation_repository.create(db_relation_data)
                
                # 添加到向量索引
                content = f"{subject.name} {relation.predicate} {obj.name}"
                metadata = {
                    "subject_id": relation.subject_id,
                    "predicate": relation.predicate,
                    "object_id": relation.object_id,
                    "description": relation.description
                }
                
                vector_id = await self.vector_manager.add_to_index(
                    content, created_relation.id, "relation", metadata
                )
                
                return self.data_converter.db_relation_to_relation(created_relation, vector_id)
                
        except EntityNotFoundError:
            # 允许EntityNotFoundError直接传播，不被包装
            raise
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
            StoreError: 获取失败时抛出
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
    
    async def get_entity_relations(self, entity_id: int, predicate: Optional[str] = None) -> List[Relation]:
        """获取实体的关系
        
        Args:
            entity_id: 实体ID
            predicate: 关系谓词过滤，可选
            
        Returns:
            List[Relation]: 关系对象列表
            
        Raises:
            StoreError: 获取失败时抛出
        """
        try:
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                relations = await entity_repository.get_entity_relations(entity_id, predicate)
                return [self.data_converter.db_relation_to_relation(r) for r in relations]
                
        except Exception as e:
            logger.error(f"获取实体关系失败: {e}")
            raise StoreError(f"获取实体关系失败: {str(e)}")
    
    async def delete_relation(self, relation_id: int) -> bool:
        """删除关系
        
        Args:
            relation_id: 要删除的关系ID
            
        Returns:
            bool: 删除成功返回True，关系不存在返回False
            
        Raises:
            StoreError: 删除失败时抛出
        """
        try:
            async with self.db_manager.get_session() as session:
                # 获取关系
                relation_repository = RelationRepository(session)
                relation = await relation_repository.get_by_id(relation_id)
                if not relation:
                    return False
                
                # 删除关系
                success = await relation_repository.delete(relation_id)
                
                # 删除向量
                if hasattr(relation, 'vector_id') and relation.vector_id:
                    await self.vector_manager.delete_vector(relation.vector_id)
                
                return success
                
        except Exception as e:
            logger.error(f"删除关系失败: {e}")
            raise StoreError(f"删除关系失败: {str(e)}")
    
    # 高级查询
    async def get_canonical_entity(self, entity_id: int) -> Optional[Entity]:
        """获取规范实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            Optional[Entity]: 规范实体对象，如果未找到则返回None
            
        Raises:
            StoreError: 获取失败时抛出
        """
        try:
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                canonical_entity = await entity_repository.get_canonical_entity(entity_id)
                if canonical_entity:
                    return self.data_converter.db_entity_to_entity(canonical_entity)
                return None
                
        except Exception as e:
            logger.error(f"获取规范实体失败: {e}")
            raise StoreError(f"获取规范实体失败: {str(e)}")
    
    async def merge_entities(self, source_id: int, target_id: int) -> Entity:
        """合并实体
        
        Args:
            source_id: 源实体ID（将被合并的实体）
            target_id: 目标实体ID（合并后的实体）
            
        Returns:
            Entity: 合并后的实体对象
            
        Raises:
            StoreError: 合并失败时抛出
        """
        try:
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                merged_entity = await entity_repository.merge_entities(source_id, target_id)
                return self.data_converter.db_entity_to_entity(merged_entity)
                
        except Exception as e:
            logger.error(f"合并实体失败: {e}")
            raise StoreError(f"合并实体失败: {str(e)}")
    
    async def get_entity_graph(self, entity_id: int, depth: int = 2) -> Dict[str, Any]:
        """获取实体图
        
        Args:
            entity_id: 中心实体ID
            depth: 图搜索深度，默认为2
            
        Returns:
            Dict[str, Any]: 实体图结构，包含中心实体、节点列表和边列表
            
        Raises:
            EntityNotFoundError: 实体未找到时抛出
            StoreError: 获取失败时抛出
        """
        try:
            entity = await self.get_entity(entity_id)
            if not entity:
                raise EntityNotFoundError(f"实体未找到: {entity_id}")
            
            # 获取直接关系
            relations = await self.get_entity_relations(entity_id)
            
            # 构建图结构
            nodes = {entity_id: entity}
            edges = []
            
            for relation in relations:
                # 添加关系边
                edges.append({
                    "id": relation.id,
                    "subject_id": relation.subject_id,
                    "predicate": relation.predicate,
                    "object_id": relation.object_id,
                    "description": relation.description
                })
                
                # 添加相关节点
                related_id = relation.object_id if relation.subject_id == entity_id else relation.subject_id
                if related_id not in nodes:
                    related_entity = await self.get_entity(related_id)
                    if related_entity:
                        nodes[related_id] = related_entity
            
            return {
                "center_entity": entity,
                "nodes": list(nodes.values()),
                "edges": edges,
                "depth": depth
            }
            
        except Exception as e:
            logger.error(f"获取实体图失败: {e}")
            raise StoreError(f"获取实体图失败: {str(e)}")
    
    async def search_graph(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索图
        
        Args:
            query: 搜索查询字符串
            limit: 返回结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 图结果列表，每个结果包含实体关系图
            
        Raises:
            StoreError: 搜索失败时抛出
        """
        try:
            # 搜索实体
            entities = await self.search_entities(query, limit=limit)
            
            # 构建图结果
            results = []
            for entity in entities:
                # 获取实体关系图
                graph = await self.get_entity_graph(entity.id, depth=1)
                results.append(graph)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索图失败: {e}")
            raise StoreError(f"搜索图失败: {str(e)}")
    
    # 向量操作
    async def add_to_vector_index(self, content: str, content_id: str, 
                                 content_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加到向量索引
        
        Args:
            content: 要索引的内容文本
            content_id: 内容ID（实体ID、关系ID或新闻事件ID）
            content_type: 内容类型（"entity"、"relation"、"news_event"）
            metadata: 可选的元数据
            
        Returns:
            str: 向量ID
            
        Raises:
            StoreError: 添加失败时抛出
        """
        return await self.vector_manager.add_to_index(content, content_id, content_type, metadata)
    
    async def search_vectors(self, query: str, content_type: Optional[str] = None,
                            top_k: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """向量搜索
        
        Args:
            query: 搜索查询字符串
            content_type: 内容类型过滤（"entity"、"relation"、"news_event"），可选
            top_k: 返回结果数量限制
            filter_dict: 过滤条件字典，当前实现不支持此参数
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表，每个结果包含内容和元数据
            
        Raises:
            StoreError: 搜索失败时抛出
        """
        # 注意：vector_manager.search_vectors 只接受 query, content_type, limit 三个参数
        # filter_dict 参数在当前实现中不被支持，需要后续扩展
        if filter_dict:
            logger.warning(f"filter_dict 参数在当前向量搜索实现中不被支持，将被忽略: {filter_dict}")
        
        return await self.vector_manager.search_vectors(query, content_type, top_k)
    
    # 新闻事件操作
    async def create_news_event(self, news_event: NewsEvent) -> NewsEvent:
        """创建新闻事件
        
        Args:
            news_event: 要创建的新闻事件对象，包含标题、内容、来源等信息
            
        Returns:
            NewsEvent: 创建后的新闻事件对象，包含分配的ID和向量ID
            
        Raises:
            StoreError: 创建失败时抛出
        """
        try:
            async with self.db_manager.get_session() as session:
                news_repository = NewsEventRepository(session)
                
                # 转换新闻事件数据
                news_event_data = {
                    "title": news_event.title,
                    "content": news_event.content,
                    "source": news_event.source,
                    "publish_time": news_event.publish_time
                }
                
                # 创建新闻事件
                created_news = await news_repository.create(news_event_data)
                
                # 添加到向量索引
                content = f"{news_event.title}: {news_event.content}"
                metadata = {
                    "title": news_event.title,
                    "source": news_event.source,
                    "publish_time": news_event.publish_time.isoformat() if news_event.publish_time else None
                }
                
                vector_id = await self.vector_manager.add_to_index(
                    content, created_news.id, "news_event", metadata
                )
                
                # 创建返回的新闻事件对象
                result_news = NewsEvent(
                    id=created_news.id,
                    title=created_news.title,
                    content=created_news.content,
                    source=created_news.source,
                    publish_time=created_news.publish_time,
                    vector_id=vector_id
                )
                
                return result_news
                
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
            StoreError: 获取失败时抛出
        """
        try:
            async with self.db_manager.get_session() as session:
                news_repository = NewsEventRepository(session)
                db_news = await news_repository.get_by_id(news_event_id)
                
                if not db_news:
                    return None
                
                # 创建新闻事件对象
                news_event = NewsEvent(
                    id=db_news.id,
                    title=db_news.title,
                    content=db_news.content,
                    source=db_news.source,
                    publish_time=db_news.publish_time,
                    vector_id=getattr(db_news, 'vector_id', None)
                )
                
                return news_event
                
        except Exception as e:
            logger.error(f"获取新闻事件失败: {e}")
            raise StoreError(f"获取新闻事件失败: {str(e)}")
    
    async def search_news_events(self, query: str, top_k: int = 10,
                                time_range: Optional[tuple] = None) -> List[SearchResult]:
        """搜索新闻事件
        
        Args:
            query: 搜索查询字符串
            top_k: 返回结果数量限制
            time_range: 时间范围过滤，格式为(start_time, end_time)，可选
            
        Returns:
            List[SearchResult]: 新闻事件搜索结果列表
            
        Raises:
            StoreError: 搜索失败时抛出
        """
        try:
            # 向量搜索新闻事件
            search_results = await self.vector_manager.search_vectors(query, "news_event", top_k)
            logger.debug(f"向量搜索结果: {search_results}")
            
            # 提取新闻事件ID
            news_ids = []
            for result in search_results:
                # 从结果ID中提取新闻事件ID
                content_id = result.get('id')
                if content_id:
                    try:
                        news_ids.append(int(content_id))
                    except (ValueError, TypeError):
                        logger.warning(f"无效的新闻事件ID格式: {content_id}")
                        continue
            
            # 获取新闻事件详细信息
            search_results_list = []
            async with self.db_manager.get_session() as session:
                news_repository = NewsEventRepository(session)
                
                for i, news_id in enumerate(news_ids):
                    news_event = await news_repository.get_by_id(news_id)
                    if news_event:
                        # 时间范围过滤
                        if time_range:
                            start_time, end_time = time_range
                            if news_event.publish_time:
                                if start_time and news_event.publish_time < start_time:
                                    continue
                                if end_time and news_event.publish_time > end_time:
                                    continue
                        
                        # 创建NewsEvent对象
                        news_event_obj = NewsEvent(
                            id=news_event.id,
                            title=news_event.title,
                            content=news_event.content,
                            source=news_event.source,
                            publish_time=news_event.publish_time,
                            vector_id=getattr(news_event, 'vector_id', None)
                        )
                        
                        # 创建SearchResult对象
                        search_result = SearchResult(
                            news_event=news_event_obj,
                            score=search_results[i].get('score', 0.0)
                        )
                        search_results_list.append(search_result)
            
            return search_results_list
            
        except Exception as e:
            logger.error(f"搜索新闻事件失败: {e}")
            raise StoreError(f"搜索新闻事件失败: {str(e)}")
    
    # 事务操作
    async def begin_transaction(self) -> None:
        """开始事务"""
        logger.warning("事务操作已废弃，使用自动事务管理")
    
    async def commit_transaction(self) -> None:
        """提交事务"""
        logger.warning("事务操作已废弃，使用自动事务管理")
    
    async def rollback_transaction(self) -> None:
        """回滚事务"""
        logger.warning("事务操作已废弃，使用自动事务管理")
    
    # 更新实体方法（符合StoreBase接口）
    async def update_entity(self, entity_id: int, updates: Dict[str, Any]) -> Entity:
        """更新实体（StoreBase接口）"""
        try:
            async with self.db_manager.get_session() as session:
                # 获取现有实体
                entity_repository = EntityRepository(session)
                existing_db_entity = await entity_repository.get_by_id(entity_id)
                if not existing_db_entity:
                    raise EntityNotFoundError(f"实体未找到: {entity_id}")
                
                # 获取向量ID用于后续向量更新
                vector_id = getattr(existing_db_entity, 'vector_id', None)
                
                # 更新数据库实体
                updated_db_entity = await entity_repository.update(entity_id, updates)
                
                # 更新向量索引（如果实体有向量ID）
                if vector_id:
                    # 构建更新内容
                    content = f"{updated_db_entity.name}: {updated_db_entity.description}"
                    metadata = {
                        "type": updated_db_entity.type,
                        "name": updated_db_entity.name,
                        "description": updated_db_entity.description,
                        "content_type": "entity"
                    }
                    
                    # 异步更新向量
                    await self.vector_manager.update_vector(vector_id, content, metadata)
                    logger.info(f"实体向量索引更新成功: entity_id={entity_id}, vector_id={vector_id}")
                
                # 转换并返回更新后的实体
                return self.data_converter.db_entity_to_entity(updated_db_entity, vector_id)
                
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"更新实体失败: {e}")
            raise StoreError(f"更新实体失败: {str(e)}")
    
    # 健康检查
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果，包含数据库和向量存储状态
            
        Raises:
            StoreError: 健康检查失败时抛出
        """
        try:
            # 数据库健康检查
            db_health = await self.db_manager.health_check()
            
            # 向量索引管理器健康检查
            vector_health = await self.vector_manager.health_check()
            
            # 整体状态
            overall_health = db_health.get("status") == "healthy" and vector_health.get("status") == "healthy"
            
            return {
                "status": "healthy" if overall_health else "unhealthy",
                "database": db_health,
                "vector_index": vector_health,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"HybridStore核心健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # 实体相似度查找功能
    async def find_similar_entities(self, entity_id: int, similarity_threshold: float = 0.7,
                                   top_k: int = 10) -> List[Dict[str, Any]]:
        """查找相似实体
        
        Args:
            entity_id: 目标实体ID
            similarity_threshold: 相似度阈值
            top_k: 返回结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 相似实体列表，包含实体和相似度分数
            
        Raises:
            EntityNotFoundError: 目标实体未找到时抛出
            StoreError: 搜索失败时抛出
        """
        return await self.entity_operations.find_similar_entities(entity_id, similarity_threshold, top_k)
    
    # 实体合并功能
    async def merge_similar_entities(self, entity_ids: List[int], target_entity_data: Dict[str, Any]) -> Entity:
        """合并相似实体
        
        Args:
            entity_ids: 要合并的实体ID列表
            target_entity_data: 目标实体的数据，包含名称、描述、类型等
            
        Returns:
            Entity: 合并后的新实体
            
        Raises:
            EntityNotFoundError: 实体未找到时抛出
            StoreError: 合并失败时抛出
        """
        return await self.entity_operations.merge_similar_entities(entity_ids, target_entity_data)
    
    # 知识图谱主体合并功能
    async def merge_knowledge_graph_subjects(self, subject_name: str, entity_type: Optional[str] = None) -> Entity:
        """合并知识图谱中的主体实体
        
        Args:
            subject_name: 主体名称
            entity_type: 实体类型过滤，可选
            
        Returns:
            Entity: 合并后的主体实体
            
        Raises:
            StoreError: 合并失败时抛出
        """
        return await self.entity_operations.merge_knowledge_graph_subjects(subject_name, entity_type)
    
    # 图遍历相关功能
    async def find_related_entities(self, entity_id: int, predicate: Optional[str] = None,
                                   max_depth: int = 2) -> List[Dict[str, Any]]:
        """查找相关实体（图遍历）
        
        Args:
            entity_id: 起始实体ID
            predicate: 关系类型过滤，可选
            max_depth: 最大搜索深度
            
        Returns:
            List[Dict[str, Any]]: 相关实体列表，包含实体和关系信息
            
        Raises:
            EntityNotFoundError: 起始实体未找到时抛出
            StoreError: 搜索失败时抛出
        """
        return await self.relation_operations.find_related_entities(entity_id, predicate, max_depth)
    
    # 关系合并功能
    async def merge_duplicate_relations(self, subject_id: int, object_id: int) -> List[Relation]:
        """合并重复关系
        
        Args:
            subject_id: 主体实体ID
            object_id: 客体实体ID
            
        Returns:
            List[Relation]: 合并后的关系列表
            
        Raises:
            EntityNotFoundError: 实体未找到时抛出
            StoreError: 合并失败时抛出
        """
        return await self.relation_operations.merge_duplicate_relations(subject_id, object_id)