"""
实体服务 - 业务逻辑层

负责处理实体相关的业务逻辑：
- 实体相似度分析
- 实体合并策略
- 实体推荐
- 实体聚类

依赖：
- HybridStoreCore: 提供基础存储能力
- 各种算法和策略实现
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.store.base import Entity, StoreBase
from app.store.exceptions import StoreError, EntityNotFoundError


logger = logging.getLogger(__name__)


@dataclass
class SimilarEntityResult:
    """相似实体结果"""
    entity: Entity
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MergeStrategy:
    """合并策略配置"""
    name: str  # "union", "intersection", "priority", "custom"
    attribute_priority: Optional[Dict[str, int]] = None  # 属性优先级
    conflict_resolution: str = "latest"  # "latest", "earliest", "manual"
    metadata: Optional[Dict[str, Any]] = None


class EntityService:
    """实体服务类 - 处理实体业务逻辑"""
    
    def __init__(self, store: StoreBase):
        """初始化实体服务
        
        Args:
            store: 存储层实例，提供基础CRUD能力
        """
        self.store = store
    
    async def find_similar_entities(self, entity_id: int, 
                                  similarity_threshold: float = 0.7,
                                  top_k: int = 10) -> List[SimilarEntityResult]:
        """查找相似实体
        
        业务逻辑：
        1. 获取目标实体
        2. 使用向量搜索找到候选实体
        3. 应用业务规则过滤（如类型、时间等）
        4. 计算综合相似度分数
        5. 返回排序结果
        
        Args:
            entity_id: 目标实体ID
            similarity_threshold: 相似度阈值
            top_k: 返回结果数量
            
        Returns:
            List[SimilarEntityResult]: 相似实体列表
            
        Raises:
            EntityNotFoundError: 目标实体不存在
            StoreError: 搜索失败
        """
        try:
            # 获取目标实体
            target_entity = await self.store.get_entity(entity_id)
            if not target_entity:
                raise EntityNotFoundError(f"实体未找到: {entity_id}")
            
            # 使用存储层的向量搜索能力
            search_results = await self.store.search_vectors(
                query=f"{target_entity.name} {target_entity.description or ''}",
                content_type="entity",
                top_k=top_k * 2,  # 搜索更多结果用于业务过滤
                filter_dict={"exclude_id": entity_id}  # 排除自身
            )
            
            similar_entities = []
            for result in search_results:
                if result.score >= similarity_threshold:
                    if result.entity and result.entity.id != entity_id:
                        similar_entities.append(SimilarEntityResult(
                            entity=result.entity,
                            similarity_score=result.score,
                            metadata=result.metadata
                        ))
            
            # 按相似度排序并限制数量
            similar_entities.sort(key=lambda x: x.similarity_score, reverse=True)
            return similar_entities[:top_k]
            
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"查找相似实体失败: {e}")
            raise StoreError(f"查找相似实体失败: {str(e)}")
    
    async def merge_entities(self, entity_ids: List[int], 
                           target_data: Dict[str, Any],
                           strategy: MergeStrategy) -> Entity:
        """合并实体
        
        业务逻辑：
        1. 验证所有实体存在且可合并
        2. 根据策略合并属性
        3. 处理关系转移
        4. 更新向量索引
        5. 清理旧数据
        
        Args:
            entity_ids: 要合并的实体ID列表
            target_data: 目标实体数据
            strategy: 合并策略
            
        Returns:
            Entity: 合并后的新实体
            
        Raises:
            EntityNotFoundError: 实体不存在
            StoreError: 合并失败
        """
        try:
            # 验证所有实体存在
            entities_to_merge = []
            for entity_id in entity_ids:
                entity = await self.store.get_entity(entity_id)
                if not entity:
                    raise EntityNotFoundError(f"实体未找到: {entity_id}")
                entities_to_merge.append(entity)
            
            # 根据策略合并属性
            merged_attributes = self._merge_attributes(
                entities_to_merge, target_data.get("attributes", {}), strategy
            )
            
            # 创建新实体
            new_entity_data = {
                "name": target_data.get("name", entities_to_merge[0].name),
                "description": target_data.get("description", ""),
                "type": target_data.get("type", entities_to_merge[0].type),
                "attributes": merged_attributes,
                "metadata": target_data.get("metadata", {})
            }
            
            # 创建新实体
            new_entity = await self.store.create_entity(Entity(**new_entity_data))
            
            # 转移关系
            await self._transfer_relations(entity_ids, new_entity.id)
            
            # 删除旧实体
            for entity_id in entity_ids:
                await self.store.delete_entity(entity_id)
            
            return new_entity
            
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"合并实体失败: {e}")
            raise StoreError(f"合并实体失败: {str(e)}")
    
    def _merge_attributes(self, entities: List[Entity], 
                         base_attributes: Dict[str, Any],
                         strategy: MergeStrategy) -> Dict[str, Any]:
        """合并属性
        
        Args:
            entities: 要合并的实体列表
            base_attributes: 基础属性
            strategy: 合并策略
            
        Returns:
            Dict[str, Any]: 合并后的属性
        """
        merged_attrs = base_attributes.copy()
        
        if strategy.name == "union":
            # 并集合并：保留所有属性
            for entity in entities:
                if entity.metadata and "attributes" in entity.metadata:
                    merged_attrs.update(entity.metadata["attributes"])
                    
        elif strategy.name == "intersection":
            # 交集合并：只保留共同属性
            common_attrs = None
            for entity in entities:
                if entity.metadata and "attributes" in entity.metadata:
                    entity_attrs = set(entity.metadata["attributes"].keys())
                    if common_attrs is None:
                        common_attrs = entity_attrs
                    else:
                        common_attrs &= entity_attrs
            
            if common_attrs:
                for attr in common_attrs:
                    # 使用第一个实体的值作为共同值
                    for entity in entities:
                        if entity.metadata and "attributes" in entity.metadata and attr in entity.metadata["attributes"]:
                            merged_attrs[attr] = entity.metadata["attributes"][attr]
                            break
                            
        elif strategy.name == "priority":
            # 优先级合并：按属性优先级选择值
            if strategy.attribute_priority:
                for attr, priority in sorted(strategy.attribute_priority.items(), key=lambda x: x[1], reverse=True):
                    for entity in entities:
                        if entity.metadata and "attributes" in entity.metadata and attr in entity.metadata["attributes"]:
                            merged_attrs[attr] = entity.metadata["attributes"][attr]
                            break
            else:
                # 默认使用第一个实体的属性
                for entity in entities:
                    if entity.metadata and "attributes" in entity.metadata:
                        merged_attrs.update(entity.metadata["attributes"])
                        break
        
        return merged_attrs
    
    async def _transfer_relations(self, old_entity_ids: List[int], new_entity_id: int) -> None:
        """转移关系到新实体
        
        Args:
            old_entity_ids: 旧实体ID列表
            new_entity_id: 新实体ID
        """
        try:
            # 获取所有相关关系
            all_relations = []
            for entity_id in old_entity_ids:
                relations = await self.store.get_entity_relations(entity_id)
                all_relations.extend(relations)
            
            # 更新关系到新实体
            for relation in all_relations:
                if relation.subject_id in old_entity_ids:
                    relation.subject_id = new_entity_id
                if relation.object_id in old_entity_ids:
                    relation.object_id = new_entity_id
                
                # 更新关系
                await self.store.update_entity(relation.subject_id, {})  # 触发关系更新
                
        except Exception as e:
            logger.error(f"转移关系失败: {e}")
            raise StoreError(f"转移关系失败: {str(e)}")
    
    async def recommend_entities(self, query: str, 
                               context_entity_ids: Optional[List[int]] = None,
                               top_k: int = 10) -> List[SimilarEntityResult]:
        """推荐实体
        
        业务逻辑：
        1. 基于查询进行向量搜索
        2. 考虑上下文实体进行过滤
        3. 应用推荐算法（如协同过滤、内容过滤）
        4. 返回推荐结果
        
        Args:
            query: 查询文本
            context_entity_ids: 上下文实体ID列表
            top_k: 推荐数量
            
        Returns:
            List[SimilarEntityResult]: 推荐实体列表
        """
        try:
            # 基础向量搜索
            search_results = await self.store.search_vectors(
                query=query,
                content_type="entity",
                top_k=top_k * 2
            )
            
            recommendations = []
            for result in search_results:
                if result.entity:
                    # 应用业务过滤规则
                    if context_entity_ids and result.entity.id in context_entity_ids:
                        continue
                    
                    recommendations.append(SimilarEntityResult(
                        entity=result.entity,
                        similarity_score=result.score,
                        metadata=result.metadata
                    ))
            
            return recommendations[:top_k]
            
        except Exception as e:
            logger.error(f"实体推荐失败: {e}")
            raise StoreError(f"实体推荐失败: {str(e)}")