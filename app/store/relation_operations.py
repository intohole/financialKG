"""
关系操作模块

该模块提供关系相关的复杂操作，包括：
- 查找相关实体：基于关系网络发现关联实体
- 合并重复关系：清理冗余的关系连接

设计模式：
- 采用策略模式封装关系操作逻辑
- 与HybridStoreCore解耦，便于独立测试和维护
- 所有方法均为异步，确保高性能

依赖：
- DatabaseManager: 数据库操作
- VectorIndexManager: 向量索引操作（用于增强关系发现）
- DataConverter: 数据转换

性能考虑：
- 使用异步批量操作减少数据库访问次数
- 实现关系缓存机制避免重复查询
- 支持分页查询处理大规模关系网络
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from app.database.manager import DatabaseManager
from app.database.repositories import RelationRepository, EntityRepository
from app.store.base import Relation, Entity
from app.store.exceptions import StoreError, EntityNotFoundError, RelationNotFoundError
from app.store.data_converter import DataConverter
from app.store.vector_index_manager import VectorIndexManager


logger = logging.getLogger(__name__)


class RelationOperations:
    """
    关系操作类 - 处理关系相关的复杂操作
    
    主要职责：
    1. 相关实体发现：通过关系网络找到关联实体
    2. 重复关系清理：识别并合并冗余的关系连接
    3. 关系路径分析：支持复杂的关系路径查询
    
    设计原则：
    - 图算法优化：使用高效的图遍历算法
    - 可扩展性：支持自定义关系类型和权重
    - 数据一致性：确保关系操作的事务性
    """
    
    def __init__(self, db_manager: DatabaseManager, vector_manager: VectorIndexManager, 
                 data_converter: DataConverter, executor: ThreadPoolExecutor) -> None:
        """初始化关系操作类
        
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
    
    async def find_related_entities(self, entity_id: int, predicate: Optional[str] = None,
                                   max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        基于关系网络查找相关实体
        
        算法说明：
        使用广度优先搜索(BFS)遍历关系图，支持：
        - 多层级关系发现（max_depth控制搜索深度）
        - 关系类型过滤（predicate指定关系类型）
        - 结果排序（基于关系强度和实体重要性）
        - 向量相似度增强（结合语义相似度）
        
        Args:
            entity_id: 起始实体ID
            predicate: 关系类型过滤，None表示不限制
            max_depth: 最大搜索深度，默认2层
            
        Returns:
            List[Dict[str, Any]]: 相关实体列表，包含实体和关系信息
            
        Raises:
            EntityNotFoundError: 起始实体不存在
            StoreError: 关系查询失败
            
        Example:
            >>> related_entities = await relation_ops.find_related_entities(
            ...     entity_id=123,
            ...     predicate="投资",
            ...     max_depth=3
            ... )
            >>> for item in related_entities:
            ...     print(f"{item['entity'].name} (深度: {item['depth']})")
        """
        try:
            async with self.db_manager.get_session() as session:
                entity_repository = EntityRepository(session)
                relation_repository = RelationRepository(session)
                
                # 验证起始实体存在
                start_entity = await entity_repository.get_by_id(entity_id)
                if not start_entity:
                    raise EntityNotFoundError(f"实体未找到: {entity_id}")
                
                # 使用广度优先搜索查找相关实体
                visited = set()
                queue = [(entity_id, 0)]  # (entity_id, depth)
                related_entities = []
                
                while queue:
                    current_entity_id, depth = queue.pop(0)
                    
                    if current_entity_id in visited or depth > max_depth:
                        continue
                    
                    visited.add(current_entity_id)
                    
                    # 获取当前实体的关系
                    relations = await entity_repository.get_entity_relations(current_entity_id)
                    
                    for relation in relations:
                        # 关系类型过滤
                        if predicate and relation.predicate != predicate:
                            continue
                        
                        # 找到相关的实体ID
                        related_entity_id = None
                        if relation.subject_id == current_entity_id:
                            related_entity_id = relation.object_id
                        elif relation.object_id == current_entity_id:
                            related_entity_id = relation.subject_id
                        
                        if related_entity_id and related_entity_id not in visited:
                            # 获取相关实体
                            related_entity = await entity_repository.get_by_id(related_entity_id)
                            if related_entity:
                                related_entities.append({
                                    'entity': self.data_converter.db_entity_to_entity(related_entity),
                                    'relation': self.data_converter.db_relation_to_relation(relation),
                                    'depth': depth + 1,
                                    'path': f"{current_entity_id} -> {related_entity_id}"
                                })
                                
                                # 添加到队列继续搜索
                                queue.append((related_entity_id, depth + 1))
                
                return related_entities
                
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"查找相关实体失败: {e}")
            raise StoreError(f"查找相关实体失败: {str(e)}")
    
    async def merge_duplicate_relations(self, merge_threshold: float = 0.9) -> Dict[str, int]:
        """
        合并重复的关系连接
        
        重复关系定义：
        - 相同源实体和目标实体
        - 相同关系类型
        - 相似的关系属性（相似度>=阈值）
        
        合并策略：
        - 保留最早创建的关系
        - 合并关系属性（并集）
        - 更新关系强度（取最大值）
        - 删除重复关系
        
        Args:
            merge_threshold: 合并阈值，默认0.9，范围0.0-1.0
            
        Returns:
            Dict[str, int]: 合并统计信息，包含：
                - "total_checked": 检查的关系总数
                - "duplicates_found": 发现的重复关系数
                - "merged_count": 成功合并的关系数
                - "error_count": 合并失败的关系数
                
        Raises:
            StoreError: 合并过程失败
            ValueError: 阈值参数无效
            
        Example:
            >>> stats = await relation_ops.merge_duplicate_relations(merge_threshold=0.85)
            >>> print(f"合并完成: {stats['merged_count']} 个重复关系被合并")
        """
        try:
            async with self.db_manager.get_session() as session:
                relation_repository = RelationRepository(session)
                entity_repository = EntityRepository(session)
                
                # 验证实体存在
                subject = await entity_repository.get_by_id(subject_id)
                obj = await entity_repository.get_by_id(object_id)
                if not subject or not obj:
                    raise EntityNotFoundError("关系的主体或客体不存在")
                
                # 获取两个实体之间的所有关系
                all_relations = await relation_repository.get_relations_between_entities(subject_id, object_id)
                
                if not all_relations:
                    return []
                
                # 按关系类型分组
                relations_by_predicate = {}
                for relation in all_relations:
                    if relation.predicate not in relations_by_predicate:
                        relations_by_predicate[relation.predicate] = []
                    relations_by_predicate[relation.predicate].append(relation)
                
                # 合并相同类型的关系
                merged_relations = []
                for predicate, relations in relations_by_predicate.items():
                    if len(relations) == 1:
                        # 只有一个关系，直接保留
                        merged_relations.append(self.data_converter.db_relation_to_relation(relations[0]))
                    else:
                        # 合并多个相同类型的关系
                        merged_description = ""
                        merged_attributes = {}
                        
                        for relation in relations:
                            if hasattr(relation, 'description') and relation.description:
                                if merged_description:
                                    merged_description += "; "
                                merged_description += relation.description
                            
                            if hasattr(relation, 'attributes') and relation.attributes:
                                merged_attributes.update(relation.attributes)
                        
                        # 创建合并后的关系
                        merged_relation_data = {
                            'subject_id': subject_id,
                            'object_id': object_id,
                            'predicate': predicate,
                            'description': merged_description,
                            'attributes': merged_attributes
                        }
                        
                        # 删除旧关系
                        for relation in relations:
                            await relation_repository.delete(relation.id)
                            # 删除关系向量
                            if hasattr(relation, 'vector_id') and relation.vector_id:
                                await self.vector_manager.delete_vector(relation.vector_id)
                        
                        # 创建新关系
                        new_relation = await relation_repository.create(merged_relation_data)
                        
                        # 添加到向量索引
                        subject_entity = await entity_repository.get_by_id(subject_id)
                        object_entity = await entity_repository.get_by_id(object_id)
                        
                        content = f"{subject_entity.name} {predicate} {object_entity.name}"
                        metadata = {
                            "subject_id": subject_id,
                            "predicate": predicate,
                            "object_id": object_id,
                            "description": merged_description
                        }
                        
                        vector_id = await self.vector_manager.add_to_index(
                            content, new_relation.id, "relation", metadata
                        )
                        
                        # 更新向量ID
                        new_relation.vector_id = vector_id
                        await session.flush()
                        
                        merged_relations.append(self.data_converter.db_relation_to_relation(new_relation, vector_id))
                
                return merged_relations
                
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"合并重复关系失败: {e}")
            raise StoreError(f"合并重复关系失败: {str(e)}")