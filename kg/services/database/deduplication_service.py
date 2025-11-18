import logging
from typing import List, Dict, Any, Optional
from kg.utils.db_utils import handle_db_errors
from kg.database.models import EntityGroup, RelationGroup
from kg.services.database.entity_service import EntityService
from kg.services.database.relation_service import RelationService

logger = logging.getLogger(__name__)

class DeduplicationService:
    """
    实体和关系去重服务
    负责处理实体和关系的重复检测与合并
    """
    
    def __init__(self, entity_service: EntityService, relation_service: RelationService):
        self.entity_service = entity_service
        self.relation_service = relation_service
    
    @handle_db_errors(default_return=[])
    async def deduplicate_entities(self, similarity_threshold: float = 0.8) -> List[EntityGroup]:
        """
        实体去重
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            List[EntityGroup]: 创建的实体分组列表
        """
        logger.info(f"开始进行实体去重，相似度阈值: {similarity_threshold}")
        
        # 获取所有实体
        all_entities = await self.entity_service.entity_repo.get_all()
        logger.info(f"获取到 {len(all_entities)} 个实体进行去重")
        
        # 按类型分组
        entities_by_type = {}
        for entity in all_entities:
            entity_type = entity.type
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        # 对每种类型的实体进行去重
        entity_groups = []
        for entity_type, entities in entities_by_type.items():
            logger.debug(f"对 {entity_type} 类型的 {len(entities)} 个实体进行去重")
            
            # 使用名称前缀分组
            name_prefixes = {}
            
            for entity in entities:
                # 使用名称的前2个字符作为前缀
                prefix = entity.name[:2]
                if prefix not in name_prefixes:
                    name_prefixes[prefix] = []
                name_prefixes[prefix].append(entity)
            
            # 对每个前缀分组进行合并
            for prefix, group_entities in name_prefixes.items():
                if len(group_entities) > 1:
                    # 选择置信度最高的实体作为主要实体
                    primary_entity = max(group_entities, key=lambda e: e.confidence_score)
                    
                    # 创建实体分组
                    entity_group = await self.entity_service.merge_entities(
                        entity_ids=[e.id for e in group_entities],
                        canonical_name=primary_entity.name,
                        description=f"合并自前缀为'{prefix}'的{entity_type}实体"
                    )
                    
                    entity_groups.append(entity_group)
        
        logger.info(f"完成实体去重，创建了 {len(entity_groups)} 个实体分组")
        return entity_groups
    
    @handle_db_errors(default_return=[])
    async def deduplicate_relations(self, similarity_threshold: float = 0.8) -> List[RelationGroup]:
        """
        关系去重
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            List[RelationGroup]: 创建的关系分组列表
        """
        logger.info(f"开始进行关系去重，相似度阈值: {similarity_threshold}")
        
        # 获取所有关系
        all_relations = await self.relation_service.relation_repo.get_all()
        logger.info(f"获取到 {len(all_relations)} 个关系进行去重")
        
        # 按实体对分组
        entity_pairs = {}
        
        for relation in all_relations:
            # 创建实体对的键（排序后确保一致性）
            source_id = relation.source_entity_id
            target_id = relation.target_entity_id
            
            # 确保source_id <= target_id，以便统一排序
            if source_id > target_id:
                source_id, target_id = target_id, source_id
            
            pair_key = f"{source_id}_{target_id}"
            
            if pair_key not in entity_pairs:
                entity_pairs[pair_key] = []
            entity_pairs[pair_key].append(relation)
        
        # 对每个实体对的关系进行去重
        relation_groups = []
        for pair_key, relations in entity_pairs.items():
            if len(relations) > 1:
                # 按关系类型分组
                relation_types = {}
                
                for relation in relations:
                    relation_type = relation.relation_type
                    if relation_type not in relation_types:
                        relation_types[relation_type] = []
                    relation_types[relation_type].append(relation)
                
                # 对每种关系类型进行合并
                for relation_type, type_relations in relation_types.items():
                    if len(type_relations) > 1:
                        # 选择权重最高的关系作为主要关系
                        primary_relation = max(type_relations, key=lambda r: r.weight)
                        
                        # 创建关系分组
                        relation_group = await self.relation_service.merge_relations(
                            relation_ids=[r.id for r in type_relations],
                            canonical_relation=relation_type,
                            description=f"合并自实体对{pair_key}的{relation_type}关系"
                        )
                        
                        relation_groups.append(relation_group)
        
        logger.info(f"完成关系去重，创建了 {len(relation_groups)} 个关系分组")
        return relation_groups