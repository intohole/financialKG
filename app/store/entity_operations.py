"""
实体操作模块

该模块提供实体相关的复杂操作，包括：
- 基于向量搜索的实体相似度查找
- 实体合并功能
- 知识图谱主体合并

设计模式：
- 采用策略模式封装实体操作逻辑
- 与HybridStoreCore解耦，便于独立测试和维护
- 所有方法均为异步，确保高性能

依赖：
- DatabaseManager: 数据库操作
- VectorIndexManager: 向量索引操作
- DataConverter: 数据转换
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor

from app.database.manager import DatabaseManager
from app.database.repositories import EntityRepository, RelationRepository
from app.store.base import Entity, SearchResult
from app.store.exceptions import StoreError, EntityNotFoundError
from app.store.data_converter import DataConverter
from app.store.vector_index_manager import VectorIndexManager


logger = logging.getLogger(__name__)


class EntityOperations:
    """
    实体操作类 - 处理实体相关的复杂操作
    
    主要职责：
    1. 实体相似度查找：基于向量搜索找到相似实体
    2. 实体合并：将多个相似实体合并为一个
    3. 知识图谱主体合并：专门处理知识图谱中的主体合并
    
    设计原则：
    - 单一职责：每个方法只负责一个具体功能
    - 错误处理：统一的异常处理机制
    - 日志记录：详细的操作日志便于调试
    """
    
    def __init__(self, db_manager: DatabaseManager, vector_manager: VectorIndexManager, 
                 data_converter: DataConverter, executor: ThreadPoolExecutor) -> None:
        """初始化实体操作类
        
        Args:
            db_manager: 数据库管理器
            vector_manager: 向量索引管理器
            data_converter: 数据转换器
            executor: 线程池执行器
        """
        self.db_manager = db_manager
        self.vector_manager = vector_manager
        self.data_converter = data_converter
        self.executor = executor
    
    async def find_similar_entities(self, entity_id: int, similarity_threshold: float = 0.7,
                                   top_k: int = 10) -> List[Dict[str, Any]]:
        """
        基于向量搜索查找相似实体
        
        算法流程：
        1. 获取目标实体的向量表示
        2. 在向量索引中搜索相似向量
        3. 过滤相似度低于阈值的实体
        4. 获取实体详细信息并返回
        
        Args:
            entity_id: 目标实体ID
            similarity_threshold: 相似度阈值，默认0.7，范围0.0-1.0
            top_k: 返回结果数量限制，默认10
            
        Returns:
            List[Dict[str, Any]]: 相似实体列表，包含实体和相似度分数，按相似度降序排列
            
        Raises:
            EntityNotFoundError: 目标实体不存在
            StoreError: 向量搜索失败
            
        Example:
            >>> similar_entities = await entity_ops.find_similar_entities(
            ...     entity_id=123,
            ...     similarity_threshold=0.8,
            ...     top_k=5
            ... )
            >>> for item in similar_entities:
            ...     print(f"{item['entity'].name} (相似度: {item['similarity_score']})")
        """
        try:
            # 获取目标实体
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                target_entity = await entity_repository.get_by_id(entity_id)
                if not target_entity:
                    raise EntityNotFoundError(f"实体未找到: {entity_id}")
                
                # 获取目标实体的向量表示
                if not hasattr(target_entity, 'vector_id') or not target_entity.vector_id:
                    logger.warning(f"实体没有向量ID: {entity_id}")
                    return []
                
                # 使用实体名称和描述生成查询向量
                query_text = f"{target_entity.name} {target_entity.description}"
                
                # 搜索相似实体
                search_results = await self.vector_manager.search_vectors(
                    query_text, "entity", top_k * 2  # 搜索更多结果用于过滤
                )
                
                similar_entities = []
                for result in search_results:
                    if result.get('score', 0) >= similarity_threshold:
                        content_id = result.get('metadata', {}).get('content_id')
                        if content_id and int(content_id) != entity_id:  # 排除自身
                            try:
                                similar_entity = await entity_repository.get_by_id(int(content_id))
                                if similar_entity:
                                    similar_entities.append({
                                        'entity': self.data_converter.db_entity_to_entity(similar_entity),
                                        'similarity_score': result['score']
                                    })
                            except (ValueError, TypeError):
                                logger.warning(f"无效的实体ID格式: {content_id}")
                                continue
                
                # 按相似度排序并限制数量
                similar_entities.sort(key=lambda x: x['similarity_score'], reverse=True)
                return similar_entities[:top_k]
                
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"查找相似实体失败: {e}")
            raise StoreError(f"查找相似实体失败: {str(e)}")
    
    async def merge_similar_entities(self, entity_ids: List[int], target_entity_data: Dict[str, Any]) -> Entity:
        """
        合并相似实体
        
        合并策略：
        - "union": 并集合并，保留所有属性和关系
        - "intersection": 交集合并，只保留共同属性
        - "priority": 优先级合并，按实体优先级保留信息
        
        合并流程：
        1. 验证所有待合并实体存在
        2. 根据策略合并实体属性
        3. 转移所有相关关系到目标实体
        4. 更新向量索引
        5. 删除源实体
        
        Args:
            entity_ids: 要合并的实体ID列表
            target_entity_data: 目标实体的数据，包含名称、描述、类型等
            
        Returns:
            Entity: 合并后的新实体
            
        Raises:
            EntityNotFoundError: 实体未找到时抛出
            StoreError: 合并失败时抛出
            
        Example:
            >>> merged_entity = await entity_ops.merge_similar_entities(
            ...     entity_ids=[123, 456],
            ...     target_entity_data={
            ...         "name": "合并后公司",
            ...         "description": "合并后的新公司",
            ...         "type": "公司",
            ...         "attributes": {"规模": "大型"}
            ...     }
            ... )
            >>> print(f"合并成功: {merged_entity.name}")
        """
        try:
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                relation_repository = RelationRepository(session)
                
                # 验证所有实体存在
                entities_to_merge = []
                for entity_id in entity_ids:
                    entity = await entity_repository.get_by_id(entity_id)
                    if not entity:
                        raise EntityNotFoundError(f"实体未找到: {entity_id}")
                    entities_to_merge.append(entity)
                
                # 创建新实体
                new_entity_data = {
                    'name': target_entity_data.get('name', entities_to_merge[0].name),
                    'description': target_entity_data.get('description', ''),
                    'type': target_entity_data.get('type', entities_to_merge[0].type),
                    'attributes': target_entity_data.get('attributes', {})
                }
                
                # 合并属性（如果有多个实体）
                if len(entities_to_merge) > 1:
                    merged_attributes = {}
                    for entity in entities_to_merge:
                        if hasattr(entity, 'attributes') and entity.attributes:
                            merged_attributes.update(entity.attributes)
                    if merged_attributes:
                        new_entity_data['attributes'].update(merged_attributes)
                
                # 创建新实体
                new_entity = await entity_repository.create(new_entity_data)
                
                # 转移关系
                all_relations = set()
                for entity in entities_to_merge:
                    entity_relations = await entity_repository.get_entity_relations(entity.id)
                    all_relations.update(entity_relations)
                
                # 更新关系到新实体
                for relation in all_relations:
                    if relation.subject_id in entity_ids:
                        relation.subject_id = new_entity.id
                    if relation.object_id in entity_ids:
                        relation.object_id = new_entity.id
                    await relation_repository.update(relation)
                
                # 添加新实体到向量索引
                content = f"{new_entity.name}: {new_entity.description}"
                metadata = {
                    "type": new_entity.type,
                    "name": new_entity.name,
                    "description": new_entity.description
                }
                
                vector_id = await self.vector_manager.add_to_index(
                    content, new_entity.id, "entity", metadata
                )
                
                # 更新新实体的向量ID
                new_entity.vector_id = vector_id
                await session.flush()
                
                # 删除旧实体
                for entity in entities_to_merge:
                    # 删除旧实体的向量
                    if hasattr(entity, 'vector_id') and entity.vector_id:
                        await self.vector_manager.delete_vector(entity.vector_id)
                    
                    # 删除旧实体
                    await entity_repository.delete(entity.id)
                
                # 返回合并后的实体
                return self.data_converter.db_entity_to_entity(new_entity, vector_id)
                
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"合并实体失败: {e}")
            raise StoreError(f"合并实体失败: {str(e)}")
    
    async def merge_knowledge_graph_subjects(self, subject_entities: List[Entity], merge_threshold: float = 0.8) -> List[Entity]:
        """
        合并知识图谱中的主体实体
        
        专门用于处理知识图谱中的主体合并，考虑知识图谱的特殊性：
        - 主体通常具有复杂的层级关系
        - 需要保持知识结构的完整性
        - 合并后需要更新所有相关的三元组
        
        合并流程：
        1. 分析主体实体的相似度
        2. 识别可合并的主体组
        3. 按组进行智能合并
        4. 更新知识图谱结构
        5. 重新生成向量索引
        
        Args:
            subject_entities: 待合并的主体实体列表
            merge_threshold: 合并阈值，默认0.8，范围0.0-1.0
            
        Returns:
            List[Entity]: 合并后的主体实体列表
            
        Raises:
            StoreError: 知识图谱合并失败
            ValueError: 参数无效
            
        Example:
            >>> subjects = [entity1, entity2, entity3]
            >>> merged_subjects = await entity_ops.merge_knowledge_graph_subjects(
            ...     subject_entities=subjects,
            ...     merge_threshold=0.85
            ... )
            >>> print(f"合并完成，剩余主体数: {len(merged_subjects)}")
        """
        try:
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                
                # 查找同名主体
                query = f"SELECT * FROM entities WHERE name = :name"
                params = {"name": subject_name}
                
                if entity_type:
                    query += " AND type = :type"
                    params["type"] = entity_type
                
                from sqlalchemy import text
                result = await session.execute(text(query), params)
                similar_entities = result.fetchall()
                
                if not similar_entities:
                    raise EntityNotFoundError(f"未找到主体: {subject_name}")
                
                if len(similar_entities) == 1:
                    # 只有一个实体，直接返回
                    return self.data_converter.db_entity_to_entity(similar_entities[0])
                
                # 合并多个相似实体
                entity_ids = [entity.id for entity in similar_entities]
                
                # 构建合并后的实体数据
                merged_description = ""
                merged_attributes = {}
                
                for entity in similar_entities:
                    if hasattr(entity, 'description') and entity.description:
                        if merged_description:
                            merged_description += "; "
                        merged_description += entity.description
                    
                    if hasattr(entity, 'attributes') and entity.attributes:
                        merged_attributes.update(entity.attributes)
                
                target_entity_data = {
                    'name': subject_name,
                    'description': merged_description or f"合并的{subject_name}实体",
                    'type': entity_type or similar_entities[0].type,
                    'attributes': merged_attributes
                }
                
                # 执行合并
                return await self.merge_similar_entities(entity_ids, target_entity_data)
                
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"合并知识图谱主体失败: {e}")
            raise StoreError(f"合并知识图谱主体失败: {str(e)}")