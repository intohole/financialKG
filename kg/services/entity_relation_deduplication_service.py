"""
实体和关系去重合并服务类
负责将LLM聚合服务与数据库操作相结合，实现自动去重和合并功能
"""
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from kg.database.models import Entity, Relation, EntityGroup, RelationGroup
from kg.database.repositories import (
    EntityRepository, RelationRepository, EntityGroupRepository, RelationGroupRepository
)
from kg.database.connection import get_db_session
from kg.utils.db_utils import handle_db_errors, handle_db_errors_with_reraise, jsonify_properties

# 导入数据库服务
from kg.services.database.entity_service import EntityService
from kg.services.database.relation_service import RelationService

# 导入LLM服务
from kg.services.llm_service import LLMService

# 导入embedding服务
from kg.services.embedding_service import create_embedding_service, EmbeddingService

# 导入Chroma向量数据库服务
from kg.services.chroma_service import create_chroma_service, ChromaService

logger = logging.getLogger(__name__)


class EntityRelationDeduplicationService:
    """实体和关系去重合并服务"""
    
    def __init__(self, session: Optional[Session] = None, llm_service: Optional[LLMService] = None,
                 embedding_service: Optional[EmbeddingService] = None, chroma_service: Optional[ChromaService] = None):
        """
        初始化去重合并服务
        
        Args:
            session: 数据库会话，如果为None则创建新会话
            llm_service: LLM服务实例，如果为None则创建新实例
            embedding_service: Embedding服务实例，如果为None则创建新实例
            chroma_service: Chroma服务实例，如果为None则创建新实例
        """
        self.session = session or get_db_session()
        self.entity_service = EntityService(self.session)
        self.relation_service = RelationService(self.session)
        self.entity_repo = EntityRepository(self.session)
        self.relation_repo = RelationRepository(self.session)
        self.entity_group_repo = EntityGroupRepository(self.session)
        self.relation_group_repo = RelationGroupRepository(self.session)
        self.llm_service = llm_service or LLMService()
        self.embedding_service = embedding_service or create_embedding_service()
        self.chroma_service = chroma_service or create_chroma_service()
    
    @handle_db_errors_with_reraise()
    async def deduplicate_entities_by_type(self, entity_type: str, 
                                         similarity_threshold: float = 0.8, 
                                         batch_size: int = 100,
                                         limit: Optional[int] = None) -> Dict[str, Any]:
        """
        根据实体类型进行去重
        
        Args:
            entity_type: 实体类型
            similarity_threshold: 相似度阈值
            batch_size: 批次大小
            limit: 处理的实体数量限制
            
        Returns:
            去重结果统计信息
        """
        logger.info(f"开始对类型为 {entity_type} 的实体进行去重，相似度阈值: {similarity_threshold}")
        
        # 从数据库获取指定类型的实体
        entities = await self.entity_service.get_entities_by_type(entity_type, limit=limit)
        logger.info(f"共获取到 {len(entities)} 个 {entity_type} 类型实体")
        
        # 转换为LLM服务需要的格式
        entities_data = []
        for entity in entities:
            properties = json.loads(entity.properties) if entity.properties else {}
            entities_data.append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "properties": properties,
                "confidence_score": entity.confidence_score or 0.0,
                "source": entity.source
            })
        
        # 批次处理
        total_duplicates = 0
        total_groups = 0
        total_processed = 0
        
        for i in range(0, len(entities_data), batch_size):
            batch = entities_data[i:i + batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}/{(len(entities_data) + batch_size - 1)//batch_size}")
            
            # 增强：使用embedding和Chroma向量搜索查找潜在重复实体
            potential_duplicate_groups = []
            
            try:
                # 1. 提取实体名称作为文本用于生成embedding
                entity_names = [entity.get("name", "") for entity in batch]
                
                # 2. 获取实体embedding
                embeddings = await self.embedding_service.get_embeddings(entity_names)
                
                # 3. 将embedding存储到Chroma向量数据库
                entity_ids = [str(entity.get("id", f"temp_{i}")) for i, entity in enumerate(batch)]
                metadata = [{"entity_type": entity.get("type", ""), "source": entity.get("source", "")} for entity in batch]
                
                await self.chroma_service.add_embeddings(
                    collection_name=f"entities_{entity_type}",
                    documents=entity_names,
                    embeddings=embeddings,
                    ids=entity_ids,
                    metadata=metadata
                )
                
                # 4. 查询相似实体
                similar_results = await self.chroma_service.query_similar_embeddings(
                    collection_name=f"entities_{entity_type}",
                    query_embeddings=embeddings,
                    n_results=10,
                    where={"entity_type": entity_type}
                )
                
                # 5. 构建潜在重复实体组
                processed_ids = set()
                for i, ids in enumerate(similar_results.get("ids", [])):
                    if not ids:
                        continue
                        
                    # 获取相似实体ID和分数
                    for j, id in enumerate(ids):
                        if id not in processed_ids and j > 0:  # 跳过自己
                            score = similar_results.get("distances", [[]])[i][j]
                            if score < (1.0 - similarity_threshold):  # 距离越小相似度越高
                                # 查找原始实体
                                original_entity = next((e for e in batch if str(e.get("id")) == id), None)
                                if original_entity:
                                    # 查找当前查询实体
                                    query_entity = batch[i]
                                    # 将这两个实体作为潜在重复组
                                    potential_duplicate_groups.append([query_entity, original_entity])
                                    processed_ids.add(id)
            except Exception as e:
                logger.error(f"使用embedding和Chroma查找潜在重复实体失败: {str(e)}")
                # 即使失败，也继续使用传统方法
            
            # 合并潜在重复实体组
            if potential_duplicate_groups:
                # 将潜在重复实体组转换为实体列表
                potential_duplicates = []
                for group in potential_duplicate_groups:
                    potential_duplicates.extend(group)
                
                # 调用LLM服务查找并合并重复实体
                duplicate_result = await self.llm_service.aggregate_entities(
                    potential_duplicates,
                    aggregation_type="duplicate",
                    similarity_threshold=similarity_threshold
                )
            else:
                # 没有潜在重复实体，直接调用LLM服务
                duplicate_result = await self.llm_service.aggregate_entities(
                    batch,
                    aggregation_type="duplicate",
                    similarity_threshold=similarity_threshold
                )
            
            # 处理重复实体组
            duplicate_groups = duplicate_result.get("duplicate_groups", [])
            total_duplicates += sum(len(group["entities"]) for group in duplicate_groups)
            total_groups += len(duplicate_groups)
            total_processed += len(batch)
            
            # 对每个重复组进行合并处理
            for group in duplicate_groups:
                await self._process_entity_duplicate_group(group, entity_type)
        
        result = {
            "entity_type": entity_type,
            "total_entities_processed": total_processed,
            "total_duplicate_groups": total_groups,
            "total_duplicate_entities": total_duplicates,
            "similarity_threshold": similarity_threshold,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"实体去重完成: {result}")
        return result
    
    @handle_db_errors_with_reraise()
    async def _process_entity_duplicate_group(self, duplicate_group: Dict[str, Any], 
                                            entity_type: str) -> EntityGroup:
        """
        处理实体重复组，创建实体组并更新实体关联
        
        Args:
            duplicate_group: 重复实体组信息
            entity_type: 实体类型
            
        Returns:
            创建的实体组
        """
        # 获取组内的实体信息
        entities_info = duplicate_group.get("entities", [])
        entity_ids = [e["id"] for e in entities_info if "id" in e]
        
        if len(entity_ids) < 2:
            logger.warning(f"实体组实体数量不足，跳过合并: {entity_ids}")
            return None
        
        # 调用LLM服务进行实体属性合并，获取规范名称
        merge_result = await self.llm_service.aggregate_entities(
            entities_info,
            aggregation_type="merge_attributes"
        )
        
        # 获取合并后的实体信息
        merged_entity = merge_result.get("merged_entity", {})
        canonical_name = merged_entity.get("canonical_name") or \
                         max(entities_info, key=lambda x: x.get("confidence_score", 0)).get("name")
        
        description = f"自动合并的{entity_type}类型实体组，包含{len(entity_ids)}个实体"
        
        # 创建实体组并合并实体
        entity_group = await self.entity_service.merge_entities(
            entity_ids=entity_ids,
            canonical_name=canonical_name,
            description=description
        )
        
        logger.info(f"已合并实体组: {canonical_name}, 包含 {len(entity_ids)} 个实体")
        return entity_group
    
    @handle_db_errors_with_reraise()
    async def deduplicate_entities_by_keyword(self, keyword: str, 
                                            similarity_threshold: float = 0.8,
                                            entity_type: Optional[str] = None,
                                            limit: Optional[int] = 100) -> Dict[str, Any]:
        """
        根据关键词搜索实体并进行去重
        
        Args:
            keyword: 搜索关键词
            similarity_threshold: 相似度阈值
            entity_type: 实体类型过滤（可选）
            limit: 处理的实体数量限制
            
        Returns:
            去重结果统计信息
        """
        logger.info(f"开始对关键词 '{keyword}' 搜索到的实体进行去重，相似度阈值: {similarity_threshold}")
        
        # 从数据库搜索实体
        entities = await self.entity_service.search_entities(keyword, entity_type, limit)
        logger.info(f"搜索到 {len(entities)} 个相关实体")
        
        if not entities:
            return {
                "keyword": keyword,
                "entity_type": entity_type,
                "total_entities_processed": 0,
                "total_duplicate_groups": 0,
                "total_duplicate_entities": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # 转换为LLM服务需要的格式
        entities_data = []
        for entity in entities:
            properties = json.loads(entity.properties) if entity.properties else {}
            entities_data.append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "properties": properties,
                "confidence_score": entity.confidence_score or 0.0,
                "source": entity.source
            })
        
        # 调用LLM服务查找重复实体
        duplicate_result = await self.llm_service.aggregate_entities(
            entities_data,
            aggregation_type="duplicate",
            similarity_threshold=similarity_threshold
        )
        
        # 处理重复实体组
        duplicate_groups = duplicate_result.get("duplicate_groups", [])
        total_duplicates = sum(len(group["entities"]) for group in duplicate_groups)
        
        for group in duplicate_groups:
            await self._process_entity_duplicate_group(group, entity_type or "mixed")
        
        result = {
            "keyword": keyword,
            "entity_type": entity_type,
            "total_entities_processed": len(entities),
            "total_duplicate_groups": len(duplicate_groups),
            "total_duplicate_entities": total_duplicates,
            "similarity_threshold": similarity_threshold,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"关键词实体去重完成: {result}")
        return result
    
    @handle_db_errors_with_reraise()
    async def deduplicate_all_entities(self, similarity_threshold: float = 0.8,
                                      batch_size: int = 100,
                                      entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        对所有实体进行去重（可按类型过滤）
        
        Args:
            similarity_threshold: 相似度阈值
            batch_size: 批次大小
            entity_types: 实体类型列表，如果为None则处理所有类型
            
        Returns:
            总体去重结果统计信息
        """
        logger.info(f"开始对所有实体进行去重，相似度阈值: {similarity_threshold}")
        
        # 如果指定了实体类型，按类型处理
        if entity_types:
            type_results = {}
            total_processed = 0
            total_groups = 0
            total_duplicates = 0
            
            for entity_type in entity_types:
                type_result = await self.deduplicate_entities_by_type(
                    entity_type=entity_type,
                    similarity_threshold=similarity_threshold,
                    batch_size=batch_size
                )
                type_results[entity_type] = type_result
                total_processed += type_result.get("total_entities_processed", 0)
                total_groups += type_result.get("total_duplicate_groups", 0)
                total_duplicates += type_result.get("total_duplicate_entities", 0)
            
            result = {
                "total_entities_processed": total_processed,
                "total_duplicate_groups": total_groups,
                "total_duplicate_entities": total_duplicates,
                "similarity_threshold": similarity_threshold,
                "entity_type_results": type_results,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 处理所有实体类型
            # 先获取所有不同的实体类型
            all_entity_types = self.entity_repo.get_all_entity_types()
            logger.info(f"系统中共有 {len(all_entity_types)} 种实体类型")
            
            type_results = {}
            total_processed = 0
            total_groups = 0
            total_duplicates = 0
            
            for entity_type in all_entity_types:
                type_result = await self.deduplicate_entities_by_type(
                    entity_type=entity_type,
                    similarity_threshold=similarity_threshold,
                    batch_size=batch_size
                )
                type_results[entity_type] = type_result
                total_processed += type_result.get("total_entities_processed", 0)
                total_groups += type_result.get("total_duplicate_groups", 0)
                total_duplicates += type_result.get("total_duplicate_entities", 0)
            
            result = {
                "total_entities_processed": total_processed,
                "total_duplicate_groups": total_groups,
                "total_duplicate_entities": total_duplicates,
                "total_entity_types": len(all_entity_types),
                "similarity_threshold": similarity_threshold,
                "entity_type_results": type_results,
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"所有实体去重完成: {result}")
        return result
    
    @handle_db_errors_with_reraise()
    async def deduplicate_relations_by_type(self, relation_type: str, 
                                          similarity_threshold: float = 0.8,
                                          batch_size: int = 100,
                                          limit: Optional[int] = None) -> Dict[str, Any]:
        """
        根据关系类型进行去重
        
        Args:
            relation_type: 关系类型
            similarity_threshold: 相似度阈值
            batch_size: 批次大小
            limit: 处理的关系数量限制
            
        Returns:
            去重结果统计信息
        """
        logger.info(f"开始对类型为 {relation_type} 的关系进行去重，相似度阈值: {similarity_threshold}")
        
        # 从数据库获取指定类型的关系
        relations = await self.relation_service.get_relations_by_type(relation_type, limit=limit)
        logger.info(f"共获取到 {len(relations)} 个 {relation_type} 类型关系")
        
        # 转换为LLM服务需要的格式
        relations_data = []
        for relation in relations:
            properties = json.loads(relation.properties) if relation.properties else {}
            
            # 获取源实体和目标实体信息
            source_entity = await self.entity_service.get_entity_by_id(relation.source_entity_id)
            target_entity = await self.entity_service.get_entity_by_id(relation.target_entity_id)
            
            relations_data.append({
                "id": relation.id,
                "source_entity_id": relation.source_entity_id,
                "target_entity_id": relation.target_entity_id,
                "relation_type": relation.relation_type,
                "properties": properties,
                "weight": relation.weight or 1.0,
                "source": relation.source,
                "source_entity": {
                    "id": source_entity.id,
                    "name": source_entity.name,
                    "type": source_entity.type
                } if source_entity else None,
                "target_entity": {
                    "id": target_entity.id,
                    "name": target_entity.name,
                    "type": target_entity.type
                } if target_entity else None
            })
        
        # 批次处理
        total_duplicates = 0
        total_groups = 0
        total_processed = 0
        
        for i in range(0, len(relations_data), batch_size):
            batch = relations_data[i:i + batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}/{(len(relations_data) + batch_size - 1)//batch_size}")
            
            # 调用LLM服务查找重复关系
            duplicate_result = await self.llm_service.aggregate_relations(
                batch,
                aggregation_type="duplicate",
                similarity_threshold=similarity_threshold
            )
            
            # 处理重复关系组
            duplicate_groups = duplicate_result.get("duplicate_groups", [])
            total_duplicates += sum(len(group["relations"]) for group in duplicate_groups)
            total_groups += len(duplicate_groups)
            total_processed += len(batch)
            
            # 对每个重复组进行合并处理
            for group in duplicate_groups:
                await self._process_relation_duplicate_group(group, relation_type)
        
        result = {
            "relation_type": relation_type,
            "total_relations_processed": total_processed,
            "total_duplicate_groups": total_groups,
            "total_duplicate_relations": total_duplicates,
            "similarity_threshold": similarity_threshold,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"关系去重完成: {result}")
        return result
    
    @handle_db_errors_with_reraise()
    async def _process_relation_duplicate_group(self, duplicate_group: Dict[str, Any],
                                              relation_type: str) -> RelationGroup:
        """
        处理关系重复组，创建关系组并更新关系关联
        
        Args:
            duplicate_group: 重复关系组信息
            relation_type: 关系类型
            
        Returns:
            创建的关系组
        """
        # 获取组内的关系信息
        relations_info = duplicate_group.get("relations", [])
        relation_ids = [r["id"] for r in relations_info if "id" in r]
        
        if len(relation_ids) < 2:
            logger.warning(f"关系组关系数量不足，跳过合并: {relation_ids}")
            return None
        
        # 调用LLM服务进行关系属性合并，获取规范关系类型
        merge_result = await self.llm_service.aggregate_relations(
            relations_info,
            aggregation_type="merge_attributes"
        )
        
        # 获取合并后的关系信息
        merged_relation = merge_result.get("merged_relation", {})
        canonical_relation = merged_relation.get("canonical_relation") or \
                            max(relations_info, key=lambda x: x.get("weight", 1.0)).get("relation_type")
        
        description = f"自动合并的{relation_type}类型关系组，包含{len(relation_ids)}个关系"
        
        # 创建关系组并合并关系
        relation_group = await self.relation_service.merge_relations(
            relation_ids=relation_ids,
            canonical_relation=canonical_relation,
            description=description
        )
        
        logger.info(f"已合并关系组: {canonical_relation}, 包含 {len(relation_ids)} 个关系")
        return relation_group
    
    @handle_db_errors_with_reraise()
    async def deduplicate_relations_by_entity(self, entity_id: int, 
                                            similarity_threshold: float = 0.8,
                                            as_source: bool = True,
                                            as_target: bool = True,
                                            relation_type: Optional[str] = None,
                                            batch_size: int = 100) -> Dict[str, Any]:
        """
        对与指定实体相关的关系进行去重
        
        Args:
            entity_id: 实体ID
            similarity_threshold: 相似度阈值
            as_source: 是否作为源实体
            as_target: 是否作为目标实体
            relation_type: 关系类型过滤（可选）
            batch_size: 批次大小
            
        Returns:
            去重结果统计信息
        """
        logger.info(f"开始对实体ID {entity_id} 相关的关系进行去重，相似度阈值: {similarity_threshold}")
        
        # 从数据库获取与指定实体相关的关系
        relations = await self.relation_service.get_relations_by_entity(
            entity_id, as_source, as_target, relation_type
        )
        logger.info(f"共获取到 {len(relations)} 个相关关系")
        
        # 转换为LLM服务需要的格式
        relations_data = []
        for relation in relations:
            properties = json.loads(relation.properties) if relation.properties else {}
            
            # 获取源实体和目标实体信息
            source_entity = await self.entity_service.get_entity_by_id(relation.source_entity_id)
            target_entity = await self.entity_service.get_entity_by_id(relation.target_entity_id)
            
            relations_data.append({
                "id": relation.id,
                "source_entity_id": relation.source_entity_id,
                "target_entity_id": relation.target_entity_id,
                "relation_type": relation.relation_type,
                "properties": properties,
                "weight": relation.weight or 1.0,
                "source": relation.source,
                "source_entity": {
                    "id": source_entity.id,
                    "name": source_entity.name,
                    "type": source_entity.type
                } if source_entity else None,
                "target_entity": {
                    "id": target_entity.id,
                    "name": target_entity.name,
                    "type": target_entity.type
                } if target_entity else None
            })
        
        # 批次处理
        total_duplicates = 0
        total_groups = 0
        total_processed = 0
        
        for i in range(0, len(relations_data), batch_size):
            batch = relations_data[i:i + batch_size]
            
            # 调用LLM服务查找重复关系
            duplicate_result = self.llm_service.aggregate_relations(
                batch,
                aggregation_type="duplicate",
                similarity_threshold=similarity_threshold
            )
            
            # 处理重复关系组
            duplicate_groups = duplicate_result.get("duplicate_groups", [])
            total_duplicates += sum(len(group["relations"]) for group in duplicate_groups)
            total_groups += len(duplicate_groups)
            total_processed += len(batch)
            
            # 对每个重复组进行合并处理
            for group in duplicate_groups:
                rel_type = group.get("relations", [{}])[0].get("relation_type", relation_type or "mixed")
                await self._process_relation_duplicate_group(group, rel_type)
        
        result = {
            "entity_id": entity_id,
            "relation_type": relation_type,
            "total_relations_processed": total_processed,
            "total_duplicate_groups": total_groups,
            "total_duplicate_relations": total_duplicates,
            "similarity_threshold": similarity_threshold,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"实体相关关系去重完成: {result}")
        return result
    
    @handle_db_errors_with_reraise()
    async def deduplicate_all_relations(self, similarity_threshold: float = 0.8,
                                      batch_size: int = 100,
                                      relation_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        对所有关系进行去重（可按类型过滤）
        
        Args:
            similarity_threshold: 相似度阈值
            batch_size: 批次大小
            relation_types: 关系类型列表，如果为None则处理所有类型
            
        Returns:
            总体去重结果统计信息
        """
        logger.info(f"开始对所有关系进行去重，相似度阈值: {similarity_threshold}")
        
        # 如果指定了关系类型，按类型处理
        if relation_types:
            type_results = {}
            total_processed = 0
            total_groups = 0
            total_duplicates = 0
            
            for rel_type in relation_types:
                type_result = await self.deduplicate_relations_by_type(
                    relation_type=rel_type,
                    similarity_threshold=similarity_threshold,
                    batch_size=batch_size
                )
                type_results[rel_type] = type_result
                total_processed += type_result.get("total_relations_processed", 0)
                total_groups += type_result.get("total_duplicate_groups", 0)
                total_duplicates += type_result.get("total_duplicate_relations", 0)
            
            result = {
                "total_relations_processed": total_processed,
                "total_duplicate_groups": total_groups,
                "total_duplicate_relations": total_duplicates,
                "similarity_threshold": similarity_threshold,
                "relation_type_results": type_results,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 处理所有关系类型
            # 先获取所有不同的关系类型
            all_relation_types = self.relation_repo.get_all_relation_types()
            logger.info(f"系统中共有 {len(all_relation_types)} 种关系类型")
            
            type_results = {}
            total_processed = 0
            total_groups = 0
            total_duplicates = 0
            
            for rel_type in all_relation_types:
                type_result = await self.deduplicate_relations_by_type(
                    relation_type=rel_type,
                    similarity_threshold=similarity_threshold,
                    batch_size=batch_size
                )
                type_results[rel_type] = type_result
                total_processed += type_result.get("total_relations_processed", 0)
                total_groups += type_result.get("total_duplicate_groups", 0)
                total_duplicates += type_result.get("total_duplicate_relations", 0)
            
            result = {
                "total_relations_processed": total_processed,
                "total_duplicate_groups": total_groups,
                "total_duplicate_relations": total_duplicates,
                "total_relation_types": len(all_relation_types),
                "similarity_threshold": similarity_threshold,
                "relation_type_results": type_results,
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"所有关系去重完成: {result}")
        return result
    
    @handle_db_errors_with_reraise()
    async def consolidate_relations_after_entity_merging(self, entity_group_id: int) -> Dict[str, Any]:
        """
        在实体合并后整合相关关系
        
        Args:
            entity_group_id: 实体组ID
            
        Returns:
            整合结果统计信息
        """
        logger.info(f"开始整合实体组ID {entity_group_id} 相关的关系")
        
        # 获取实体组中的所有实体
        entities_in_group = await self.entity_service.get_entities_by_group(entity_group_id)
        logger.info(f"实体组中共有 {len(entities_in_group)} 个实体")
        
        # 获取主实体（用于关系整合）
        entity_group = self.entity_group_repo.get(entity_group_id)
        primary_entity = None
        if entity_group and entity_group.primary_entity_id:
            primary_entity = await self.entity_service.get_entity_by_id(entity_group.primary_entity_id)
        
        if not primary_entity and entities_in_group:
            # 如果没有指定主实体，选择第一个实体
            primary_entity = entities_in_group[0]
        
        if not primary_entity:
            logger.error(f"无法找到实体组 {entity_group_id} 的主实体")
            return {
                "entity_group_id": entity_group_id,
                "status": "error",
                "message": "无法找到主实体",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"选择主实体: {primary_entity.name} (ID: {primary_entity.id})")
        
        # 收集所有与组内实体相关的关系
        all_relations = []
        for entity in entities_in_group:
            # 获取该实体作为源或目标的所有关系
            relations = await self.relation_service.get_relations_by_entity(
                entity.id, as_source=True, as_target=True
            )
            all_relations.extend(relations)
        
        # 去重关系列表
        unique_relations = {rel.id: rel for rel in all_relations}.values()
        logger.info(f"收集到 {len(unique_relations)} 个相关关系")
        
        # 转换为LLM服务需要的格式
        relations_data = []
        for relation in unique_relations:
            properties = json.loads(relation.properties) if relation.properties else {}
            
            # 获取源实体和目标实体信息
            source_entity = await self.entity_service.get_entity_by_id(relation.source_entity_id)
            target_entity = await self.entity_service.get_entity_by_id(relation.target_entity_id)
            
            relations_data.append({
                "id": relation.id,
                "source_entity_id": relation.source_entity_id,
                "target_entity_id": relation.target_entity_id,
                "relation_type": relation.relation_type,
                "properties": properties,
                "weight": relation.weight or 1.0,
                "source": relation.source,
                "source_entity": {
                    "id": source_entity.id,
                    "name": source_entity.name,
                    "type": source_entity.type
                } if source_entity else None,
                "target_entity": {
                    "id": target_entity.id,
                    "name": target_entity.name,
                    "type": target_entity.type
                } if target_entity else None
            })
        
        # 准备实体数据用于整合
        entities_data = []
        for entity in entities_in_group:
            entities_data.append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "is_primary": entity.id == primary_entity.id
            })
        
        # 调用LLM服务进行关系整合
        consolidate_result = self.llm_service.aggregate_relations(
            relations_data,
            aggregation_type="consolidate",
            entities=entities_data
        )
        
        # 处理整合后的关系
        consolidated_relations = consolidate_result.get("consolidated_relations", [])
        
        # 记录统计信息
        total_relations_processed = len(relations_data)
        total_relations_consolidated = len(consolidated_relations)
        
        # 这里可以添加具体的关系更新逻辑
        # 例如：更新关系中的实体引用为主实体，合并重复关系等
        
        logger.info(f"关系整合完成，处理了 {total_relations_processed} 个关系，整合为 {total_relations_consolidated} 个关系")
        
        return {
            "entity_group_id": entity_group_id,
            "primary_entity_id": primary_entity.id,
            "primary_entity_name": primary_entity.name,
            "total_relations_processed": total_relations_processed,
            "total_relations_consolidated": total_relations_consolidated,
            "timestamp": datetime.now().isoformat()
        }
    
    @handle_db_errors_with_reraise()
    async def full_deduplication(self, similarity_threshold: float = 0.8,
                                batch_size: int = 100,
                                entity_types: Optional[List[str]] = None,
                                relation_types: Optional[List[str]] = None,
                                skip_entities: bool = False,
                                skip_relations: bool = False) -> Dict[str, Any]:
        """
        执行完整的实体和关系去重流程
        
        Args:
            similarity_threshold: 相似度阈值
            batch_size: 批次大小
            entity_types: 实体类型列表（可选）
            relation_types: 关系类型列表（可选）
            skip_entities: 是否跳过实体去重
            skip_relations: 是否跳过关系去重
            
        Returns:
            完整去重结果统计信息
        """
        logger.info(f"开始执行完整去重流程，相似度阈值: {similarity_threshold}")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "similarity_threshold": similarity_threshold
        }
        
        # 执行实体去重
        if not skip_entities:
            entity_result = await self.deduplicate_all_entities(
                similarity_threshold=similarity_threshold,
                batch_size=batch_size,
                entity_types=entity_types
            )
            results["entity_deduplication"] = entity_result
        
        # 执行关系去重
        if not skip_relations:
            relation_result = await self.deduplicate_all_relations(
                similarity_threshold=similarity_threshold,
                batch_size=batch_size,
                relation_types=relation_types
            )
            results["relation_deduplication"] = relation_result
        
        logger.info(f"完整去重流程执行完成")
        return results
