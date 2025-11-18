import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from kg.database.models import Entity, Relation, RelationGroup
from kg.database.repositories import (
    RelationRepository, RelationGroupRepository
)
from kg.database.connection import get_db_session
from kg.utils.db_utils import handle_db_errors, handle_db_errors_with_reraise, jsonify_properties
from .entity_service import EntityService

# 配置日志
logger = logging.getLogger(__name__)

class RelationService:
    """关系服务类，提供关系相关的高级操作"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_db_session()
        self.relation_repo = RelationRepository(self.session)
        self.relation_group_repo = RelationGroupRepository(self.session)
        self.entity_service = EntityService(self.session)
    
    @handle_db_errors_with_reraise()
    def create_relation(self, source_entity_id: int, target_entity_id: int, 
                       relation_type: str, canonical_relation: Optional[str] = None,
                       properties: Optional[Dict[str, Any]] = None, weight: float = 1.0,
                       source: Optional[str] = None) -> Relation:
        """
        创建关系
        
        Args:
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID
            relation_type: 关系类型
            canonical_relation: 规范关系类型
            properties: 关系属性
            weight: 关系权重
            source: 关系来源
            
        Returns:
            Relation: 创建的关系对象
        """
        relation = self.relation_repo.create(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relation_type=relation_type,
            canonical_relation=canonical_relation,
            properties=jsonify_properties(properties),
            weight=weight,
            source=source
        )
        logger.info(f"创建关系成功: {relation_type} (ID: {relation.id})")
        return relation
    
    @handle_db_errors_with_reraise()
    async def get_or_create_relation(self, source_entity_id: int, target_entity_id: int, 
                              relation_type: str, canonical_relation: Optional[str] = None,
                              properties: Optional[Dict[str, Any]] = None, weight: float = 1.0,
                              source: Optional[str] = None) -> Relation:
        """
        获取或创建关系
        
        Args:
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID
            relation_type: 关系类型
            canonical_relation: 规范关系类型
            properties: 关系属性
            weight: 关系权重
            source: 关系来源
            
        Returns:
            Relation: 获取或创建的关系对象
        """
        relation = await self.relation_repo.get_or_create(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relation_type=relation_type,
            canonical_relation=canonical_relation,
            properties=jsonify_properties(properties),
            weight=weight,
            source=source
        )
        logger.debug(f"获取或创建关系: {relation_type} (ID: {relation.id})")
        return relation
    
    @handle_db_errors(default_return=[])
    def find_similar_relations(self, source_entity_id: int, target_entity_id: int, 
                              relation_type: str, threshold: float = 0.8) -> List[Relation]:
        """
        查找相似关系
        
        Args:
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID
            relation_type: 关系类型
            threshold: 相似度阈值
            
        Returns:
            List[Relation]: 相似的关系列表
        """
        # 查找相同实体对之间的所有关系
        relations = self.relation_repo.find_by_entities(source_entity_id, target_entity_id)
        
        # 过滤出相同类型的关系
        same_type_relations = [r for r in relations if r.relation_type == relation_type]
        
        # 这里可以添加更精确的相似度计算
        # 返回相似度大于阈值的关系
        return same_type_relations
    
    @handle_db_errors_with_reraise()
    def merge_relations(self, relation_ids: List[int], canonical_relation: str, 
                       description: Optional[str] = None) -> RelationGroup:
        """
        合并关系，创建关系分组
        
        Args:
            relation_ids: 要合并的关系ID列表
            canonical_relation: 合并后的规范关系类型
            description: 分组描述
            
        Returns:
            RelationGroup: 创建的关系分组对象
        """
        # 创建关系分组
        relation_group = self.relation_group_repo.create(
            group_name=canonical_relation,
            description=description
        )
        
        # 更新所有关系的分组ID和规范关系类型
        for relation_id in relation_ids:
            relation = self.relation_repo.get(relation_id)
            if relation:
                self.relation_repo.update(
                    relation_id,
                    relation_group_id=relation_group.id,
                    canonical_relation=canonical_relation
                )
        
        logger.info(f"合并关系成功: {canonical_relation}, 包含 {len(relation_ids)} 个关系")
        return relation_group
    
    @handle_db_errors(default_return=None)
    def get_relation_by_id(self, relation_id: int) -> Optional[Relation]:
        """根据ID获取关系"""
        return self.relation_repo.get(relation_id)
    
    @handle_db_errors(default_return=[])
    def get_relations_by_group(self, relation_group_id: int) -> List[Relation]:
        """根据分组ID获取关系"""
        return self.relation_repo.find_by_group_id(relation_group_id)
    
    @handle_db_errors(default_return=[])
    def get_relations_by_type(self, relation_type: str, limit: Optional[int] = None) -> List[Relation]:
        """根据类型获取关系"""
        return self.relation_repo.find_by_type(relation_type, limit)
    
    @handle_db_errors(default_return=[])
    def get_relations_by_entity(self, entity_id: int, as_source: bool = True, 
                               as_target: bool = True, relation_type: Optional[str] = None) -> List[Relation]:
        """
        根据实体ID获取关系
        
        Args:
            entity_id: 实体ID
            as_source: 是否作为源实体
            as_target: 是否作为目标实体
            relation_type: 关系类型过滤
            
        Returns:
            List[Relation]: 关系列表
        """
        relations = []
        
        if as_source:
            relations.extend(self.relation_repo.find_by_source_entity(entity_id, relation_type))
        
        if as_target:
            relations.extend(self.relation_repo.find_by_target_entity(entity_id, relation_type))
        
        return relations
    
    @handle_db_errors(default_return=[])
    def get_entity_relations(self, source_entity_id: int, target_entity_id: int) -> List[Relation]:
        """获取两个实体之间的关系"""
        return self.relation_repo.find_by_entities(source_entity_id, target_entity_id)
    
    @handle_db_errors(default_return=None)
    def update_relation(self, relation_id: int, **kwargs) -> Optional[Relation]:
        """更新关系"""
        if 'properties' in kwargs and kwargs['properties']:
            kwargs['properties'] = json.dumps(kwargs['properties'])
        return self.relation_repo.update(relation_id, **kwargs)
