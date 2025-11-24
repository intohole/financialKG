"""
数据转换工具模块
负责数据库模型和业务模型之间的转换
"""

from typing import Optional, Dict, Any
from app.database.models import Entity as DBEntity, Relation as DBRelation
from app.store.store_base_abstract import Entity, Relation


class DataConverter:
    """数据转换工具类 - 负责数据库模型和业务模型之间的转换"""
    
    @staticmethod
    def db_entity_to_entity(db_entity: DBEntity, vector_id: Optional[str] = None) -> Entity:
        """数据库实体转换为业务实体"""
        if db_entity is None:
            raise ValueError("数据库实体不能为None")
        
        try:
            return Entity(
                id=db_entity.id,
                name=db_entity.name,
                type=db_entity.type,
                description=db_entity.description,
                canonical_id=db_entity.canonical_id,
                created_at=db_entity.created_at,
                updated_at=db_entity.updated_at,
                vector_id=vector_id,
                metadata=getattr(db_entity, 'meta_data', None)
            )
        except AttributeError as e:
            raise ValueError(f"数据库实体缺少必要属性: {e}")
    
    @staticmethod
    def entity_to_db_entity(entity: Entity) -> Dict[str, Any]:
        """业务实体转换为数据库实体数据字典"""
        if entity is None:
            raise ValueError("业务实体不能为None")
        
        result = {
            'name': entity.name,
            'type': entity.type,
            'description': entity.description,
            'canonical_id': entity.canonical_id
        }
        
        # 如果metadata存在且不为None，添加到结果中
        if hasattr(entity, 'metadata') and entity.metadata is not None:
            result['meta_data'] = entity.metadata
        
        # 如果vector_id存在且不为None，添加到结果中
        if hasattr(entity, 'vector_id') and entity.vector_id is not None:
            result['vector_id'] = entity.vector_id
            
        return result
    
    @staticmethod
    def db_relation_to_relation(db_relation: DBRelation, vector_id: Optional[str] = None) -> Relation:
        """数据库关系转换为业务关系"""
        if db_relation is None:
            raise ValueError("数据库关系不能为None")
        
        try:
            return Relation(
                id=db_relation.id,
                subject_id=db_relation.subject_id,
                predicate=db_relation.predicate,
                object_id=db_relation.object_id,
                description=db_relation.description,
                created_at=db_relation.created_at,
                vector_id=vector_id,
                metadata=getattr(db_relation, 'meta_data', None)
            )
        except AttributeError as e:
            raise ValueError(f"数据库关系缺少必要属性: {e}")
    
    @staticmethod
    def relation_to_db_relation(relation: Relation) -> Dict[str, Any]:
        """业务关系转换为数据库关系数据字典"""
        if relation is None:
            raise ValueError("业务关系不能为None")
        
        result = {
            'subject_id': relation.subject_id,
            'predicate': relation.predicate,
            'object_id': relation.object_id,
            'description': relation.description
        }
        
        # 如果metadata存在且不为None，添加到结果中
        if hasattr(relation, 'metadata') and relation.metadata is not None:
            result['meta_data'] = relation.metadata
            
        return result