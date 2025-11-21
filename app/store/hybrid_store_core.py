"""
HybridStore核心模块
包含HybridStore主类和核心逻辑
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor

from app.database.manager import DatabaseManager
from app.database.repositories import EntityRepository, RelationRepository
from app.store.base import StoreBase, Entity, Relation, NewsEvent, StoreConfig
from app.store.exceptions import StoreError, EntityNotFoundError, RelationNotFoundError
from app.store.data_converter import DataConverter
from app.store.vector_index_manager import VectorIndexManager
from app.vector.base import VectorSearchBase
from app.embedding import EmbeddingService


logger = logging.getLogger(__name__)


class HybridStoreCore(StoreBase):
    """HybridStore核心类 - 整合Chroma向量数据库和SQLAlchemy关系型数据库"""
    
    def __init__(self, db_manager: DatabaseManager, vector_store: VectorSearchBase, 
                 embedding_service: EmbeddingService, executor: ThreadPoolExecutor):
        """初始化HybridStore核心"""
        self.db_manager = db_manager
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.executor = executor
        
        # 初始化工具
        self.vector_manager = VectorIndexManager(vector_store, embedding_service, executor)
        self.data_converter = DataConverter()
        
        self._initialized = False
    
    async def initialize(self, config: Optional[StoreConfig] = None):
        """初始化存储"""
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
    
    async def close(self):
        """关闭存储"""
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
        """创建实体"""
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
                
                # 转换回业务实体
                return self.data_converter.db_entity_to_entity(created_entity, vector_id)
                
        except Exception as e:
            logger.error(f"创建实体失败: {e}")
            raise StoreError(f"创建实体失败: {str(e)}")
    
    async def get_entity(self, entity_id: int) -> Optional[Entity]:
        """获取实体"""
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
    
    async def update_entity(self, entity: Entity) -> Entity:
        """更新实体"""
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
        """删除实体"""
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
                             limit: int = 10) -> List[Entity]:
        """搜索实体"""
        try:
            # 向量搜索
            results = await self.vector_manager.search_vectors(query, "entity", limit)
            
            # 获取实体ID
            entity_ids = [r['content_id'] for r in results]
            
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
        """创建关系"""
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
                
        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            raise StoreError(f"创建关系失败: {str(e)}")
    
    async def get_relation(self, relation_id: int) -> Optional[Relation]:
        """获取关系"""
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
        """获取实体的关系"""
        try:
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                relations = await entity_repository.get_entity_relations(entity_id, predicate)
                return [self.data_converter.db_relation_to_relation(r) for r in relations]
                
        except Exception as e:
            logger.error(f"获取实体关系失败: {e}")
            raise StoreError(f"获取实体关系失败: {str(e)}")
    
    async def delete_relation(self, relation_id: int) -> bool:
        """删除关系"""
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
        """获取规范实体"""
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
        """合并实体"""
        try:
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                merged_entity = await entity_repository.merge_entities(source_id, target_id)
                return self.data_converter.db_entity_to_entity(merged_entity)
                
        except Exception as e:
            logger.error(f"合并实体失败: {e}")
            raise StoreError(f"合并实体失败: {str(e)}")
    
    async def get_entity_graph(self, entity_id: int, depth: int = 2) -> Dict[str, Any]:
        """获取实体图"""
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
        """搜索图"""
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
        """添加到向量索引"""
        return await self.vector_manager.add_to_index(content, content_id, content_type, metadata)
    
    async def search_vectors(self, query: str, content_type: Optional[str] = None,
                            top_k: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """向量搜索"""
        return await self.vector_manager.search_vectors(query, content_type, top_k, filter_dict)
    
    # 新闻事件操作
    async def create_news_event(self, news_event: NewsEvent) -> NewsEvent:
        """创建新闻事件"""
        # 这里简化实现，实际应该调用相应的新闻事件仓库
        logger.warning("新闻事件创建功能未实现")
        return news_event
    
    async def get_news_event(self, news_event_id: int) -> Optional[NewsEvent]:
        """获取新闻事件"""
        logger.warning("新闻事件获取功能未实现")
        return None
    
    async def search_news_events(self, query: str, top_k: int = 10,
                                time_range: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """搜索新闻事件"""
        logger.warning("新闻事件搜索功能未实现")
        return []
    
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
        # 获取现有实体
        existing_entity = await self.get_entity(str(entity_id))
        if not existing_entity:
            raise EntityNotFoundError(f"实体未找到: {entity_id}")
        
        # 更新实体属性
        for key, value in updates.items():
            if hasattr(existing_entity, key):
                setattr(existing_entity, key, value)
        
        # 使用内部更新逻辑（避免递归）
        try:
            # 获取原始实体
            original_entity = await self.entity_repository.get_entity(str(entity_id))
            if not original_entity:
                raise EntityNotFoundError(f"实体未找到: {entity_id}")
            
            # 更新数据库实体
            db_entity = self.data_converter.entity_to_db_entity(existing_entity)
            updated_entity = await self.entity_repository.update_entity(db_entity)
            
            # 更新向量索引
            content = f"{existing_entity.name}: {existing_entity.description}"
            metadata = {
                "type": existing_entity.type,
                "name": existing_entity.name,
                "description": existing_entity.description
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
    
    # 健康检查
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
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
                "timestamp": "2024-01-01T00:00:00Z"  # 这里应该使用实际的datetime
            }
            
        except Exception as e:
            logger.error(f"HybridStore核心健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }