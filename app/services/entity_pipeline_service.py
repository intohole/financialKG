"""
实体管理管道服务 - 实体生命周期管理

负责实体的标准化、消歧、合并、质量评估等生命周期管理，
提供实体标准化处理和质量保证机制。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime

from app.core.entity_analyzer import EntityAnalyzer
from app.store.hybrid_store_core_implement import HybridStoreCore
from app.services.service_models import EntityDisambiguation, EntitySimilarity


logger = logging.getLogger(__name__)


@dataclass
class EntityStandardizationResult:
    """实体标准化结果"""
    success: bool
    original_entity: Dict[str, Any]
    standardized_entity: Dict[str, Any]
    disambiguation_score: float
    similar_entities: List[EntitySimilarity]
    processing_time: float
    errors: List[str]


@dataclass
class EntityMergeResult:
    """实体合并结果"""
    success: bool
    merged_entity: Dict[str, Any]
    source_entities: List[Dict[str, Any]]
    merge_score: float
    conflicts_resolved: List[str]
    processing_time: float
    errors: List[str]


@dataclass
class EntityQualityResult:
    """实体质量评估结果"""
    entity_id: str
    entity_name: str
    quality_score: float
    completeness_score: float
    consistency_score: float
    accuracy_score: float
    issues: List[str]
    suggestions: List[str]
    assessment_time: float


class EntityPipelineService:
    """实体管理管道服务"""
    
    def __init__(
        self,
        entity_analyzer: EntityAnalyzer,
        store: HybridStoreCore
    ):
        self.entity_analyzer = entity_analyzer
        self.store = store
        
        logger.info("实体管理管道服务初始化完成")
    
    async def standardize_entity(
        self,
        entity: Dict[str, Any],
        enable_disambiguation: bool = True,
        similarity_threshold: float = 0.8,
        context: Optional[Dict[str, Any]] = None
    ) -> EntityStandardizationResult:
        """
        标准化单个实体
        
        Args:
            entity: 原始实体数据
            enable_disambiguation: 是否启用实体消歧
            similarity_threshold: 相似度阈值
            context: 上下文信息
            
        Returns:
            标准化结果
        """
        start_time = asyncio.get_event_loop().time()
        errors = []
        
        try:
            logger.info(f"开始标准化实体: {entity.get('name', 'unknown')}")
            
            # 1. 实体基础验证
            validation_result = await self._validate_entity(entity)
            if not validation_result['valid']:
                errors.extend(validation_result['errors'])
                return EntityStandardizationResult(
                    success=False,
                    original_entity=entity,
                    standardized_entity=entity,
                    disambiguation_score=0.0,
                    similar_entities=[],
                    processing_time=asyncio.get_event_loop().time() - start_time,
                    errors=errors
                )
            
            # 2. 实体名称标准化
            standardized_name = await self._standardize_entity_name(entity.get('name', ''))
            entity['standardized_name'] = standardized_name
            
            # 3. 实体类型标准化
            standardized_type = await self._standardize_entity_type(entity.get('type', 'unknown'))
            entity['standardized_type'] = standardized_type
            
            # 4. 实体消歧
            similar_entities = []
            disambiguation_score = 1.0
            
            if enable_disambiguation:
                disambiguation_result = await self._disambiguate_entity(
                    entity, similarity_threshold, context
                )
                if disambiguation_result['success']:
                    similar_entities = disambiguation_result['similar_entities']
                    disambiguation_score = disambiguation_result['disambiguation_score']
                    if disambiguation_result.get('standardized_entity'):
                        entity.update(disambiguation_result['standardized_entity'])
            
            # 5. 属性标准化
            standardized_properties = await self._standardize_entity_properties(
                entity.get('properties', {})
            )
            entity['standardized_properties'] = standardized_properties
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = EntityStandardizationResult(
                success=True,
                original_entity=entity,
                standardized_entity=entity,
                disambiguation_score=disambiguation_score,
                similar_entities=similar_entities,
                processing_time=processing_time,
                errors=errors
            )
            
            logger.info(f"实体标准化完成，耗时: {processing_time:.2f}s，"
                       f"消歧分数: {disambiguation_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"实体标准化失败: {str(e)}", exc_info=True)
            errors.append(f"标准化过程异常: {str(e)}")
            
            return EntityStandardizationResult(
                success=False,
                original_entity=entity,
                standardized_entity=entity,
                disambiguation_score=0.0,
                similar_entities=[],
                processing_time=asyncio.get_event_loop().time() - start_time,
                errors=errors
            )
    
    async def merge_similar_entities(
        self,
        entities: List[Dict[str, Any]],
        merge_threshold: float = 0.85,
        conflict_resolution: str = "priority_based"
    ) -> List[EntityMergeResult]:
        """
        合并相似实体
        
        Args:
            entities: 实体列表
            merge_threshold: 合并阈值
            conflict_resolution: 冲突解决策略
            
        Returns:
            合并结果列表
        """
        start_time = asyncio.get_event_loop().time()
        merge_results = []
        
        try:
            logger.info(f"开始合并相似实体，总数: {len(entities)}")
            
            # 1. 实体分组
            entity_groups = await self._group_similar_entities(entities, merge_threshold)
            logger.debug(f"实体分组完成，共 {len(entity_groups)} 组")
            
            # 2. 每组内实体合并
            for group_id, group_entities in enumerate(entity_groups):
                if len(group_entities) <= 1:
                    continue  # 跳过单实体组
                
                merge_result = await self._merge_entity_group(
                    group_entities, conflict_resolution
                )
                merge_results.append(merge_result)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"实体合并完成，耗时: {processing_time:.2f}s，"
                       f"合并结果: {len(merge_results)}")
            
            return merge_results
            
        except Exception as e:
            logger.error(f"实体合并失败: {str(e)}", exc_info=True)
            return []
    
    async def assess_entity_quality(
        self,
        entity_id: str,
        quality_criteria: Optional[Dict[str, Any]] = None
    ) -> Optional[EntityQualityResult]:
        """
        评估实体质量
        
        Args:
            entity_id: 实体ID
            quality_criteria: 质量标准配置
            
        Returns:
            质量评估结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 1. 获取实体信息
            entity = await self.store.get_entity(entity_id)
            if not entity:
                logger.warning(f"实体不存在: {entity_id}")
                return None
            
            # 2. 质量评估
            quality_scores = await self._calculate_quality_scores(entity, quality_criteria)
            
            # 3. 问题识别
            issues = await self._identify_quality_issues(entity, quality_scores)
            
            # 4. 改进建议
            suggestions = await self._generate_quality_suggestions(entity, issues)
            
            assessment_time = asyncio.get_event_loop().time() - start_time
            
            result = EntityQualityResult(
                entity_id=entity_id,
                entity_name=entity.get('name', ''),
                quality_score=quality_scores['overall'],
                completeness_score=quality_scores['completeness'],
                consistency_score=quality_scores['consistency'],
                accuracy_score=quality_scores['accuracy'],
                issues=issues,
                suggestions=suggestions,
                assessment_time=assessment_time
            )
            
            logger.info(f"实体质量评估完成，ID: {entity_id}, "
                       f"质量分数: {quality_scores['overall']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"实体质量评估失败: {str(e)}", exc_info=True)
            return None
    
    async def cleanup_duplicate_entities(
        self,
        entity_type: Optional[str] = None,
        similarity_threshold: float = 0.9,
        cleanup_strategy: str = "merge_preferred"
    ) -> Dict[str, Any]:
        """
        清理重复实体
        
        Args:
            entity_type: 实体类型，None表示所有类型
            similarity_threshold: 相似度阈值
            cleanup_strategy: 清理策略
            
        Returns:
            清理结果统计
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(f"开始清理重复实体，类型: {entity_type or 'all'}")
            
            # 1. 获取所有实体
            entities = await self._get_entities_for_cleanup(entity_type)
            logger.debug(f"获取实体 {len(entities)} 个")
            
            # 2. 识别重复实体
            duplicate_groups = await self._identify_duplicates(
                entities, similarity_threshold
            )
            
            # 3. 执行清理
            cleanup_stats = await self._execute_cleanup(
                duplicate_groups, cleanup_strategy
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = {
                'total_entities': len(entities),
                'duplicate_groups': len(duplicate_groups),
                'entities_processed': cleanup_stats['processed'],
                'entities_removed': cleanup_stats['removed'],
                'entities_merged': cleanup_stats['merged'],
                'processing_time': processing_time
            }
            
            logger.info(f"重复实体清理完成，耗时: {processing_time:.2f}s，"
                       f"处理: {cleanup_stats['processed']}, "
                       f"移除: {cleanup_stats['removed']}")
            
            return result
            
        except Exception as e:
            logger.error(f"重复实体清理失败: {str(e)}", exc_info=True)
            return {
                'error': str(e),
                'processing_time': asyncio.get_event_loop().time() - start_time
            }
    
    async def _validate_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """验证实体有效性"""
        errors = []
        
        # 基本验证
        if not entity.get('name') or len(entity['name'].strip()) < 1:
            errors.append("实体名称为空")
        
        if not entity.get('type') or entity.get('type') == 'unknown':
            errors.append("实体类型未知")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    async def _standardize_entity_name(self, name: str) -> str:
        """标准化实体名称"""
        if not name:
            return name
        
        # 去除多余空格
        standardized = ' '.join(name.split())
        
        # 移除特殊字符
        import re
        standardized = re.sub(r'[^\w\s\-_.]', '', standardized)
        
        return standardized.strip()
    
    async def _standardize_entity_type(self, entity_type: str) -> str:
        """标准化实体类型"""
        type_mapping = {
            'person': '人物',
            'organization': '组织',
            'company': '公司',
            'location': '地点',
            'product': '产品',
            'event': '事件',
            'industry': '行业',
            'technology': '技术'
        }
        
        return type_mapping.get(entity_type.lower(), entity_type)
    
    async def _disambiguate_entity(
        self, 
        entity: Dict[str, Any], 
        threshold: float,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """实体消歧"""
        try:
            entity_name = entity.get('name', '')
            entity_type = entity.get('type', 'unknown')
            
            # 查找相似实体
            similar_entities = await self.entity_analyzer.find_similar_entities(
                entity_name=entity_name,
                entity_type=entity_type,
                limit=10
            )
            
            if not similar_entities:
                return {
                    'success': True,
                    'disambiguation_score': 1.0,
                    'similar_entities': [],
                    'standardized_entity': None
                }
            
            # 选择最佳匹配
            best_match = similar_entities[0]
            disambiguation_score = best_match.similarity_score
            
            if disambiguation_score >= threshold:
                return {
                    'success': True,
                    'disambiguation_score': disambiguation_score,
                    'similar_entities': similar_entities,
                    'standardized_entity': {
                        'name': best_match.entity_name,
                        'type': best_match.entity_type,
                        'properties': getattr(best_match, 'properties', {})
                    }
                }
            else:
                return {
                    'success': True,
                    'disambiguation_score': disambiguation_score,
                    'similar_entities': similar_entities,
                    'standardized_entity': None
                }
                
        except Exception as e:
            logger.error(f"实体消歧失败: {str(e)}")
            return {
                'success': False,
                'disambiguation_score': 0.0,
                'similar_entities': [],
                'standardized_entity': None
            }
    
    async def _standardize_entity_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """标准化实体属性"""
        standardized = {}
        
        # 基本属性标准化
        for key, value in properties.items():
            if isinstance(value, str):
                standardized[key] = value.strip()
            elif isinstance(value, (int, float, bool)):
                standardized[key] = value
            elif isinstance(value, list):
                standardized[key] = [str(v).strip() if isinstance(v, str) else v for v in value]
            else:
                standardized[key] = str(value)
        
        return standardized
    
    async def _group_similar_entities(
        self, 
        entities: List[Dict[str, Any]], 
        threshold: float
    ) -> List[List[Dict[str, Any]]]:
        """分组相似实体"""
        groups = []
        processed = set()
        
        for i, entity in enumerate(entities):
            if i in processed:
                continue
            
            current_group = [entity]
            processed.add(i)
            
            # 查找相似实体
            for j, other_entity in enumerate(entities[i+1:], i+1):
                if j in processed:
                    continue
                
                similarity = await self._calculate_entity_similarity(entity, other_entity)
                if similarity >= threshold:
                    current_group.append(other_entity)
                    processed.add(j)
            
            if len(current_group) > 1:
                groups.append(current_group)
        
        return groups
    
    async def _calculate_entity_similarity(
        self, 
        entity1: Dict[str, Any], 
        entity2: Dict[str, Any]
    ) -> float:
        """计算实体相似度"""
        try:
            name1 = entity1.get('name', '')
            name2 = entity2.get('name', '')
            type1 = entity1.get('type', '')
            type2 = entity2.get('type', '')
            
            # 使用实体分析器计算相似度
            similarity_result = await self.entity_analyzer.compare_entities(
                entity1_name=name1,
                entity1_type=type1,
                entity2_name=name2,
                entity2_type=type2
            )
            
            return similarity_result.similarity_score if similarity_result else 0.0
            
        except Exception as e:
            logger.error(f"计算实体相似度失败: {str(e)}")
            return 0.0
    
    async def _merge_entity_group(
        self, 
        entities: List[Dict[str, Any]], 
        conflict_resolution: str
    ) -> EntityMergeResult:
        """合并实体组"""
        start_time = asyncio.get_event_loop().time()
        errors = []
        
        try:
            # 选择主实体（通常选择第一个或最完整的）
            primary_entity = self._select_primary_entity(entities)
            
            # 解决冲突
            conflicts_resolved = await self._resolve_entity_conflicts(
                entities, primary_entity, conflict_resolution
            )
            
            # 合并属性
            merged_properties = await self._merge_entity_properties(
                entities, primary_entity
            )
            
            primary_entity['properties'] = merged_properties
            primary_entity['merged_from'] = [e.get('id') for e in entities if e.get('id')]
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return EntityMergeResult(
                success=True,
                merged_entity=primary_entity,
                source_entities=entities,
                merge_score=0.9,  # 可以基于相似度计算
                conflicts_resolved=conflicts_resolved,
                processing_time=processing_time,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"实体组合并失败: {str(e)}")
            errors.append(f"合并过程异常: {str(e)}")
            
            return EntityMergeResult(
                success=False,
                merged_entity=entities[0] if entities else {},
                source_entities=entities,
                merge_score=0.0,
                conflicts_resolved=[],
                processing_time=asyncio.get_event_loop().time() - start_time,
                errors=errors
            )
    
    def _select_primary_entity(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """选择主实体"""
        # 选择属性最完整的实体作为主实体
        best_entity = entities[0]
        max_properties = len(best_entity.get('properties', {}))
        
        for entity in entities[1:]:
            prop_count = len(entity.get('properties', {}))
            if prop_count > max_properties:
                best_entity = entity
                max_properties = prop_count
        
        return best_entity.copy()
    
    async def _resolve_entity_conflicts(
        self, 
        entities: List[Dict[str, Any]], 
        primary_entity: Dict[str, Any], 
        strategy: str
    ) -> List[str]:
        """解决实体冲突"""
        conflicts_resolved = []
        
        # 这里可以实现更复杂的冲突解决逻辑
        # 目前使用简单的优先级策略
        if strategy == "priority_based":
            # 主实体优先级最高
            conflicts_resolved.append("采用主实体属性")
        
        return conflicts_resolved
    
    async def _merge_entity_properties(
        self, 
        entities: List[Dict[str, Any]], 
        primary_entity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并实体属性"""
        merged_properties = primary_entity.get('properties', {}).copy()
        
        for entity in entities:
            if entity == primary_entity:
                continue
            
            for key, value in entity.get('properties', {}).items():
                if key not in merged_properties or not merged_properties[key]:
                    merged_properties[key] = value
        
        return merged_properties
    
    async def _calculate_quality_scores(
        self, 
        entity: Dict[str, Any], 
        criteria: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """计算质量分数"""
        # 完整性分数
        completeness = self._calculate_completeness(entity)
        
        # 一致性分数
        consistency = self._calculate_consistency(entity)
        
        # 准确性分数（这里使用简化计算）
        accuracy = 0.8  # 可以基于验证规则计算
        
        # 综合分数
        overall = (completeness + consistency + accuracy) / 3.0
        
        return {
            'overall': overall,
            'completeness': completeness,
            'consistency': consistency,
            'accuracy': accuracy
        }
    
    def _calculate_completeness(self, entity: Dict[str, Any]) -> float:
        """计算完整性分数"""
        required_fields = ['name', 'type']
        properties = entity.get('properties', {})
        
        completed_fields = 0
        total_fields = len(required_fields) + 3  # 基础字段 + 额外属性
        
        for field in required_fields:
            if entity.get(field):
                completed_fields += 1
        
        # 检查重要属性
        important_props = ['description', 'aliases', 'category']
        for prop in important_props:
            if prop in properties and properties[prop]:
                completed_fields += 1
        
        return min(1.0, completed_fields / total_fields)
    
    def _calculate_consistency(self, entity: Dict[str, Any]) -> float:
        """计算一致性分数"""
        # 简化的一致性检查
        name = entity.get('name', '')
        entity_type = entity.get('type', '')
        
        if not name or not entity_type:
            return 0.5
        
        # 检查名称和类型是否匹配（可以扩展为更复杂的规则）
        if len(name) < 2:
            return 0.7
        
        return 0.9
    
    async def _identify_quality_issues(
        self, 
        entity: Dict[str, Any], 
        quality_scores: Dict[str, float]
    ) -> List[str]:
        """识别质量问题"""
        issues = []
        
        if quality_scores['completeness'] < 0.7:
            issues.append("实体信息不完整")
        
        if quality_scores['consistency'] < 0.8:
            issues.append("实体信息不一致")
        
        if quality_scores['accuracy'] < 0.8:
            issues.append("实体信息准确性存疑")
        
        return issues
    
    async def _generate_quality_suggestions(
        self, 
        entity: Dict[str, Any], 
        issues: List[str]
    ) -> List[str]:
        """生成质量改进建议"""
        suggestions = []
        
        for issue in issues:
            if "不完整" in issue:
                suggestions.append("补充实体的描述信息和别名")
            elif "不一致" in issue:
                suggestions.append("检查实体名称和类型的一致性")
            elif "准确性" in issue:
                suggestions.append("验证实体信息的准确性")
        
        return suggestions
    
    async def _get_entities_for_cleanup(self, entity_type: Optional[str]) -> List[Dict[str, Any]]:
        """获取需要清理的实体"""
        # 这里可以实现具体的查询逻辑
        # 目前返回空列表，需要从存储中获取
        return []
    
    async def _identify_duplicates(
        self, 
        entities: List[Dict[str, Any]], 
        threshold: float
    ) -> List[List[Dict[str, Any]]]:
        """识别重复实体"""
        duplicate_groups = []
        processed = set()
        
        for i, entity in enumerate(entities):
            if i in processed:
                continue
            
            current_group = [entity]
            processed.add(i)
            
            for j, other_entity in enumerate(entities[i+1:], i+1):
                if j in processed:
                    continue
                
                similarity = await self._calculate_entity_similarity(entity, other_entity)
                if similarity >= threshold:
                    current_group.append(other_entity)
                    processed.add(j)
            
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
        
        return duplicate_groups
    
    async def _execute_cleanup(
        self, 
        duplicate_groups: List[List[Dict[str, Any]]], 
        strategy: str
    ) -> Dict[str, int]:
        """执行清理操作"""
        stats = {
            'processed': 0,
            'removed': 0,
            'merged': 0
        }
        
        for group in duplicate_groups:
            stats['processed'] += len(group)
            
            if strategy == "merge_preferred":
                # 合并实体
                merge_result = await self._merge_entity_group(group, "priority_based")
                if merge_result.success:
                    stats['merged'] += len(group) - 1
                    stats['removed'] += len(group) - 1
        
        return stats