"""
实体和关系处理工具模块

提供实体和关系提取、验证、聚合等通用功能
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .embedding_utils import calculate_cosine_similarity

logger = logging.getLogger(__name__)


def validate_entity(entity: Dict[str, Any]) -> bool:
    """
    验证实体数据格式

    Args:
        entity: 实体数据字典

    Returns:
        bool: 实体数据是否有效
    """
    try:
        # 检查必需字段
        required_fields = ["id", "name", "type"]
        if not all(field in entity for field in required_fields):
            return False

        # 检查字段类型
        if not isinstance(entity["id"], str) or not entity["id"].strip():
            return False

        if not isinstance(entity["name"], str) or not entity["name"].strip():
            return False

        if not isinstance(entity["type"], str) or not entity["type"].strip():
            return False

        # 可选字段验证
        if "metadata" in entity and not isinstance(entity["metadata"], dict):
            return False

        if "embedding" in entity and not isinstance(entity["embedding"], list):
            return False

        return True

    except Exception as e:
        logger.error(f"验证实体时发生错误: {str(e)}")
        return False


def validate_relation(relation: Dict[str, Any], entities: List[Dict[str, Any]]) -> bool:
    """
    验证关系数据格式

    Args:
        relation: 关系数据字典
        entities: 实体列表，用于验证头尾实体ID

    Returns:
        bool: 关系数据是否有效
    """
    try:
        # 检查必需字段
        required_fields = ["id", "type", "head_id", "tail_id"]
        if not all(field in relation for field in required_fields):
            return False

        # 检查字段类型
        if not isinstance(relation["id"], str) or not relation["id"].strip():
            return False

        if not isinstance(relation["type"], str) or not relation["type"].strip():
            return False

        if not isinstance(relation["head_id"], str) or not isinstance(
            relation["tail_id"], str
        ):
            return False

        # 验证头尾实体是否存在
        entity_ids = {entity["id"] for entity in entities}
        if (
            relation["head_id"] not in entity_ids
            or relation["tail_id"] not in entity_ids
        ):
            return False

        # 可选字段验证
        if "properties" in relation and not isinstance(relation["properties"], dict):
            return False

        return True

    except Exception as e:
        logger.error(f"验证关系时发生错误: {str(e)}")
        return False


def group_entities_by_type(
    entities: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    按类型分组实体

    Args:
        entities: 实体列表

    Returns:
        Dict[str, List[Dict[str, Any]]]: 按类型分组的实体字典
    """
    try:
        grouped = {}
        for entity in entities:
            if validate_entity(entity):
                entity_type = entity["type"]
                if entity_type not in grouped:
                    grouped[entity_type] = []
                grouped[entity_type].append(entity)
        return grouped

    except Exception as e:
        logger.error(f"分组实体时发生错误: {str(e)}")
        return {}


def find_entity_by_id(
    entities: List[Dict[str, Any]], entity_id: str
) -> Optional[Dict[str, Any]]:
    """
    通过ID查找实体

    Args:
        entities: 实体列表
        entity_id: 实体ID

    Returns:
        Optional[Dict[str, Any]]: 找到的实体或None
    """
    try:
        for entity in entities:
            if entity.get("id") == entity_id:
                return entity
        return None

    except Exception as e:
        logger.error(f"查找实体时发生错误: {str(e)}")
        return None


def deduplicate_entities_by_name(
    entities: List[Dict[str, Any]], case_sensitive: bool = False
) -> List[Dict[str, Any]]:
    """
    根据名称去重实体

    Args:
        entities: 实体列表
        case_sensitive: 是否区分大小写

    Returns:
        List[Dict[str, Any]]: 去重后的实体列表
    """
    try:
        seen_names = set()
        unique_entities = []

        for entity in entities:
            if validate_entity(entity):
                name = entity["name"]
                if not case_sensitive:
                    name = name.lower()

                if name not in seen_names:
                    seen_names.add(name)
                    unique_entities.append(entity)

        return unique_entities

    except Exception as e:
        logger.error(f"实体去重时发生错误: {str(e)}")
        return entities


def deduplicate_relations(relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    去重关系

    Args:
        relations: 关系列表

    Returns:
        List[Dict[str, Any]]: 去重后的关系列表
    """
    try:
        seen = set()
        unique_relations = []

        for relation in relations:
            # 使用头ID、尾ID和类型作为去重键
            if "head_id" in relation and "tail_id" in relation and "type" in relation:
                key = (relation["head_id"], relation["tail_id"], relation["type"])
                if key not in seen:
                    seen.add(key)
                    unique_relations.append(relation)

        return unique_relations

    except Exception as e:
        logger.error(f"关系去重时发生错误: {str(e)}")
        return relations


def find_entity_duplicates(
    entities: List[Dict[str, Any]], similarity_threshold: float = 0.8
) -> List[List[int]]:
    """
    查找实体重复组

    Args:
        entities: 实体列表
        similarity_threshold: 相似度阈值

    Returns:
        List[List[int]]: 包含索引的重复项组列表
    """
    try:
        duplicates = []
        visited = [False] * len(entities)

        # 筛选有效实体
        valid_entities = [
            (i, entity)
            for i, entity in enumerate(entities)
            if validate_entity(entity) and "embedding" in entity
        ]

        for i, (idx1, entity1) in enumerate(valid_entities):
            if visited[idx1]:
                continue

            duplicate_group = [idx1]
            visited[idx1] = True

            for j in range(i + 1, len(valid_entities)):
                idx2, entity2 = valid_entities[j]
                if not visited[idx2]:
                    try:
                        # 计算实体嵌入向量的相似度
                        similarity = calculate_cosine_similarity(
                            entity1["embedding"], entity2["embedding"]
                        )
                        if similarity >= similarity_threshold:
                            duplicate_group.append(idx2)
                            visited[idx2] = True
                    except Exception as e:
                        logger.debug(f"计算实体相似度失败: {str(e)}")

            if len(duplicate_group) > 1:
                duplicates.append(duplicate_group)

        return duplicates

    except Exception as e:
        logger.error(f"查找实体重复时发生错误: {str(e)}")
        return []


def merge_entity_duplicates(duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    合并重复实体

    Args:
        duplicates: 重复实体列表

    Returns:
        Dict[str, Any]: 合并后的实体
    """
    try:
        if not duplicates:
            return {}

        # 筛选有效实体
        valid_duplicates = [entity for entity in duplicates if validate_entity(entity)]
        if not valid_duplicates:
            return {}

        # 使用第一个实体作为基础
        merged = valid_duplicates[0].copy()

        # 合并元数据
        merged_metadata = merged.get("metadata", {}).copy()
        for entity in valid_duplicates[1:]:
            if "metadata" in entity:
                for key, value in entity["metadata"].items():
                    if key not in merged_metadata or not merged_metadata[key]:
                        merged_metadata[key] = value

        merged["metadata"] = merged_metadata

        # 合并计数（如果存在）
        total_count = sum(entity.get("count", 1) for entity in valid_duplicates)
        merged["count"] = total_count

        # 记录来源ID
        source_ids = [entity["id"] for entity in valid_duplicates]
        merged["source_ids"] = source_ids

        return merged

    except Exception as e:
        logger.error(f"合并实体重复时发生错误: {str(e)}")
        return duplicates[0] if duplicates else {}


def create_id_mapping(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    创建ID到项目的映射字典

    Args:
        items: 包含id字段的字典列表

    Returns:
        Dict[str, Dict[str, Any]]: 以id为键，项目为值的映射字典
    """
    try:
        return {item.get("id"): item for item in items if "id" in item}
    except Exception as e:
        logger.error(f"创建ID映射时发生错误: {str(e)}")
        return {}


def enrich_entity_with_relation_info(
    entity: Dict[str, Any],
    relations: List[Dict[str, Any]],
    all_entities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    使用关系信息丰富实体数据

    Args:
        entity: 目标实体
        relations: 关系列表
        all_entities: 所有实体列表

    Returns:
        Dict[str, Any]: 丰富后的实体
    """
    try:
        enriched = entity.copy()
        if not validate_entity(entity):
            return enriched

        # 查找以该实体为头的关系
        outgoing_relations = []
        # 查找以该实体为尾的关系
        incoming_relations = []

        entity_id = entity["id"]
        entity_dict = {e["id"]: e for e in all_entities}

        for relation in relations:
            if relation.get("head_id") == entity_id:
                # 丰富关系信息，添加尾实体名称
                rel_copy = relation.copy()
                tail_entity = entity_dict.get(relation["tail_id"])
                if tail_entity:
                    rel_copy["tail_name"] = tail_entity.get("name", "")
                    rel_copy["tail_type"] = tail_entity.get("type", "")
                outgoing_relations.append(rel_copy)

            if relation.get("tail_id") == entity_id:
                # 丰富关系信息，添加头实体名称
                rel_copy = relation.copy()
                head_entity = entity_dict.get(relation["head_id"])
                if head_entity:
                    rel_copy["head_name"] = head_entity.get("name", "")
                    rel_copy["head_type"] = head_entity.get("type", "")
                incoming_relations.append(rel_copy)

        enriched["outgoing_relations"] = outgoing_relations
        enriched["incoming_relations"] = incoming_relations
        enriched["relation_count"] = len(outgoing_relations) + len(incoming_relations)

        return enriched

    except Exception as e:
        logger.error(f"丰富实体关系信息时发生错误: {str(e)}")
        return entity
