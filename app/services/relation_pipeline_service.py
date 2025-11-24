"""
关系管理管道服务 - 关系生命周期管理

负责关系的验证、去重、权重计算、质量评估等生命周期管理，
提供关系标准化处理和质量保证机制。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.store.hybrid_store_core_implement import HybridStoreCore


logger = logging.getLogger(__name__)


@dataclass
class RelationValidationResult:
    """关系验证结果"""
    relation: Dict[str, Any]
    is_valid: bool
    validation_score: float
    issues: List[str]
    suggestions: List[str]
    validation_time: float


@dataclass
class RelationDeduplicationResult:
    """关系去重结果"""
    success: bool
    original_count: int
    deduplicated_count: int
    removed_relations: List[Dict[str, Any]]
    merged_relations: List[Dict[str, Any]]
    processing_time: float
    errors: List[str]


@dataclass
class RelationQualityResult:
    """关系质量评估结果"""
    relation_id: str
    source_entity: str
    target_entity: str
    relation_type: str
    quality_score: float
    semantic_score: float
    structural_score: float
    temporal_score: float
    issues: List[str]
    suggestions: List[str]
    assessment_time: float


class RelationPipelineService:
    """关系管理管道服务"""
    
    def __init__(self, store: HybridStoreCore):
        self.store = store
        
        # 预定义的有效关系类型
        self.valid_relation_types = {
            '所属', '位于', '涉及', '影响', '导致', '参与', '拥有', '生产',
            '销售', '合作', '竞争', '投资', '收购', '合并', '子公司',
            '母公司', '股东', '高管', '员工', '客户', '供应商',
            '关联', '控股', '参股', '子公司', '分公司', '事业部'
        }
        
        # 关系类型语义规则
        self.relation_semantic_rules = {
            '人物-公司': ['高管', '股东', '员工', '客户'],
            '公司-公司': ['合作', '竞争', '投资', '收购', '合并', '子公司', '母公司'],
            '公司-产品': ['生产', '销售', '拥有'],
            '产品-行业': ['所属', '涉及'],
            '事件-公司': ['影响', '涉及', '导致'],
            '地点-公司': ['位于', '涉及']
        }
        
        logger.info("关系管理管道服务初始化完成")
    
    async def validate_relation(
        self,
        relation: Dict[str, Any],
        enable_semantic_check: bool = True,
        enable_structural_check: bool = True,
        enable_temporal_check: bool = True
    ) -> RelationValidationResult:
        """
        验证单个关系
        
        Args:
            relation: 关系数据
            enable_semantic_check: 是否启用语义检查
            enable_structural_check: 是否启用结构检查
            enable_temporal_check: 是否启用时序检查
            
        Returns:
            验证结果
        """
        start_time = asyncio.get_event_loop().time()
        issues = []
        suggestions = []
        
        try:
            logger.info(f"开始验证关系: {relation.get('source_entity', '')} -> "
                       f"{relation.get('target_entity', '')}")
            
            # 1. 基础验证
            basic_validation = await self._validate_basic_relation(relation)
            if not basic_validation['valid']:
                issues.extend(basic_validation['issues'])
                return RelationValidationResult(
                    relation=relation,
                    is_valid=False,
                    validation_score=0.0,
                    issues=issues,
                    suggestions=suggestions,
                    validation_time=asyncio.get_event_loop().time() - start_time
                )
            
            # 2. 语义验证
            semantic_score = 1.0
            if enable_semantic_check:
                semantic_validation = await self._validate_relation_semantics(relation)
                if semantic_validation['issues']:
                    issues.extend(semantic_validation['issues'])
                    suggestions.extend(semantic_validation['suggestions'])
                    semantic_score = semantic_validation['score']
            
            # 3. 结构验证
            structural_score = 1.0
            if enable_structural_check:
                structural_validation = await self._validate_relation_structure(relation)
                if structural_validation['issues']:
                    issues.extend(structural_validation['issues'])
                    suggestions.extend(structural_validation['suggestions'])
                    structural_score = structural_validation['score']
            
            # 4. 时序验证
            temporal_score = 1.0
            if enable_temporal_check and relation.get('timestamp'):
                temporal_validation = await self._validate_relation_temporal(relation)
                if temporal_validation['issues']:
                    issues.extend(temporal_validation['issues'])
                    temporal_score = temporal_validation['score']
            
            # 5. 综合评分
            validation_score = (semantic_score + structural_score + temporal_score) / 3.0
            is_valid = validation_score >= 0.7 and len(issues) == 0
            
            validation_time = asyncio.get_event_loop().time() - start_time
            
            result = RelationValidationResult(
                relation=relation,
                is_valid=is_valid,
                validation_score=validation_score,
                issues=issues,
                suggestions=suggestions,
                validation_time=validation_time
            )
            
            logger.info(f"关系验证完成，耗时: {validation_time:.2f}s，"
                       f"分数: {validation_score:.2f}, 有效: {is_valid}")
            
            return result
            
        except Exception as e:
            logger.error(f"关系验证失败: {str(e)}", exc_info=True)
            issues.append(f"验证过程异常: {str(e)}")
            
            return RelationValidationResult(
                relation=relation,
                is_valid=False,
                validation_score=0.0,
                issues=issues,
                suggestions=suggestions,
                validation_time=asyncio.get_event_loop().time() - start_time
            )
    
    async def deduplicate_relations(
        self,
        relations: List[Dict[str, Any]],
        deduplication_threshold: float = 0.85,
        merge_strategy: str = "confidence_weighted"
    ) -> RelationDeduplicationResult:
        """
        关系去重
        
        Args:
            relations: 关系列表
            deduplication_threshold: 去重阈值
            merge_strategy: 合并策略
            
        Returns:
            去重结果
        """
        start_time = asyncio.get_event_loop().time()
        errors = []
        
        try:
            original_count = len(relations)
            logger.info(f"开始关系去重，原始数量: {original_count}")
            
            # 1. 关系分组
            relation_groups = await self._group_similar_relations(
                relations, deduplication_threshold
            )
            
            # 2. 每组内关系合并
            deduplicated_relations = []
            removed_relations = []
            
            for group in relation_groups:
                if len(group) == 1:
                    # 唯一关系，直接保留
                    deduplicated_relations.append(group[0])
                else:
                    # 合并重复关系
                    merged_relation = await self._merge_relations(
                        group, merge_strategy
                    )
                    if merged_relation:
                        deduplicated_relations.append(merged_relation)
                        removed_relations.extend(group[1:])  # 保留第一个，移除其余
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = RelationDeduplicationResult(
                success=True,
                original_count=original_count,
                deduplicated_count=len(deduplicated_relations),
                removed_relations=removed_relations,
                merged_relations=deduplicated_relations,
                processing_time=processing_time,
                errors=errors
            )
            
            logger.info(f"关系去重完成，耗时: {processing_time:.2f}s，"
                       f"原始: {original_count}, 去重后: {len(deduplicated_relations)}")
            
            return result
            
        except Exception as e:
            logger.error(f"关系去重失败: {str(e)}", exc_info=True)
            errors.append(f"去重过程异常: {str(e)}")
            
            return RelationDeduplicationResult(
                success=False,
                original_count=len(relations),
                deduplicated_count=len(relations),
                removed_relations=[],
                merged_relations=[],
                processing_time=asyncio.get_event_loop().time() - start_time,
                errors=errors
            )
    
    async def assess_relation_quality(
        self,
        relation_id: str,
        quality_criteria: Optional[Dict[str, Any]] = None
    ) -> Optional[RelationQualityResult]:
        """
        评估关系质量
        
        Args:
            relation_id: 关系ID
            quality_criteria: 质量标准配置
            
        Returns:
            质量评估结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 1. 获取关系信息
            relation = await self.store.get_relation(relation_id)
            if not relation:
                logger.warning(f"关系不存在: {relation_id}")
                return None
            
            # 2. 质量评估
            quality_scores = await self._calculate_relation_quality_scores(
                relation, quality_criteria
            )
            
            # 3. 问题识别
            issues = await self._identify_relation_quality_issues(
                relation, quality_scores
            )
            
            # 4. 改进建议
            suggestions = await self._generate_relation_quality_suggestions(
                relation, issues
            )
            
            assessment_time = asyncio.get_event_loop().time() - start_time
            
            result = RelationQualityResult(
                relation_id=relation_id,
                source_entity=relation.get('source_entity', ''),
                target_entity=relation.get('target_entity', ''),
                relation_type=relation.get('relation_type', ''),
                quality_score=quality_scores['overall'],
                semantic_score=quality_scores['semantic'],
                structural_score=quality_scores['structural'],
                temporal_score=quality_scores['temporal'],
                issues=issues,
                suggestions=suggestions,
                assessment_time=assessment_time
            )
            
            logger.info(f"关系质量评估完成，ID: {relation_id}, "
                       f"质量分数: {quality_scores['overall']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"关系质量评估失败: {str(e)}", exc_info=True)
            return None
    
    async def cleanup_invalid_relations(
        self,
        cleanup_threshold: float = 0.5,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        清理无效关系
        
        Args:
            cleanup_threshold: 清理阈值
            batch_size: 批处理大小
            
        Returns:
            清理结果统计
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(f"开始清理无效关系，阈值: {cleanup_threshold}")
            
            # 1. 获取所有关系
            all_relations = await self._get_all_relations()
            logger.debug(f"获取关系 {len(all_relations)} 个")
            
            # 2. 验证关系
            invalid_relations = []
            for relation in all_relations:
                validation_result = await self.validate_relation(
                    relation, enable_semantic_check=True
                )
                if not validation_result.is_valid or validation_result.validation_score < cleanup_threshold:
                    invalid_relations.append({
                        'relation': relation,
                        'validation_result': validation_result
                    })
            
            # 3. 执行清理
            cleanup_stats = await self._execute_relation_cleanup(invalid_relations)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = {
                'total_relations': len(all_relations),
                'invalid_relations': len(invalid_relations),
                'removed_relations': cleanup_stats['removed'],
                'updated_relations': cleanup_stats['updated'],
                'processing_time': processing_time
            }
            
            logger.info(f"无效关系清理完成，耗时: {processing_time:.2f}s，"
                       f"移除: {cleanup_stats['removed']}, "
                       f"更新: {cleanup_stats['updated']}")
            
            return result
            
        except Exception as e:
            logger.error(f"无效关系清理失败: {str(e)}", exc_info=True)
            return {
                'error': str(e),
                'processing_time': asyncio.get_event_loop().time() - start_time
            }
    
    async def _validate_basic_relation(self, relation: Dict[str, Any]) -> Dict[str, Any]:
        """基础关系验证"""
        issues = []
        
        # 检查必要字段
        required_fields = ['source_entity', 'target_entity', 'relation_type']
        for field in required_fields:
            if not relation.get(field):
                issues.append(f"缺少必要字段: {field}")
        
        # 检查关系类型
        relation_type = relation.get('relation_type', '')
        if relation_type and relation_type not in self.valid_relation_types:
            issues.append(f"无效的关系类型: {relation_type}")
        
        # 检查自引用
        source = relation.get('source_entity', '')
        target = relation.get('target_entity', '')
        if source and target and source == target:
            issues.append("关系不能自引用")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    async def _validate_relation_semantics(self, relation: Dict[str, Any]) -> Dict[str, Any]:
        """关系语义验证"""
        issues = []
        suggestions = []
        score = 1.0
        
        try:
            source_entity = relation.get('source_entity', '')
            target_entity = relation.get('target_entity', '')
            relation_type = relation.get('relation_type', '')
            
            # 获取实体类型（这里需要从存储中查询）
            source_type = await self._get_entity_type(source_entity)
            target_type = await self._get_entity_type(target_entity)
            
            # 检查语义规则
            type_pair = f"{source_type}-{target_type}"
            if type_pair in self.relation_semantic_rules:
                valid_relations = self.relation_semantic_rules[type_pair]
                if relation_type not in valid_relations:
                    issues.append(f"关系类型 '{relation_type}' 不适用于 "
                              f"'{type_pair}' 实体对")
                    suggestions.append(f"建议使用以下关系类型: {', '.join(valid_relations)}")
                    score = 0.6
            
            return {
                'score': score,
                'issues': issues,
                'suggestions': suggestions
            }
            
        except Exception as e:
            logger.error(f"关系语义验证失败: {str(e)}")
            return {
                'score': 0.5,
                'issues': [f"语义验证异常: {str(e)}"],
                'suggestions': []
            }
    
    async def _validate_relation_structure(self, relation: Dict[str, Any]) -> Dict[str, Any]:
        """关系结构验证"""
        issues = []
        suggestions = []
        score = 1.0
        
        # 检查属性完整性
        properties = relation.get('properties', {})
        if not properties:
            issues.append("关系缺少属性信息")
            suggestions.append("建议添加关系的置信度、来源等属性")
            score = 0.8
        
        # 检查置信度
        confidence = properties.get('confidence', 0)
        if confidence < 0.5:
            issues.append("关系置信度过低")
            suggestions.append("建议提高关系提取的置信度")
            score = min(score, 0.7)
        
        # 检查来源信息
        if not properties.get('source'):
            issues.append("关系缺少来源信息")
            suggestions.append("建议添加关系来源")
            score = min(score, 0.9)
        
        return {
            'score': score,
            'issues': issues,
            'suggestions': suggestions
        }
    
    async def _validate_relation_temporal(self, relation: Dict[str, Any]) -> Dict[str, Any]:
        """关系时序验证"""
        issues = []
        score = 1.0
        
        try:
            # 获取关系时间戳
            relation_time = relation.get('timestamp')
            if not relation_time:
                return {'score': score, 'issues': issues}
            
            # 检查实体存在时间
            source_exists = await self._check_entity_exists_at_time(
                relation.get('source_entity', ''), relation_time
            )
            target_exists = await self._check_entity_exists_at_time(
                relation.get('target_entity', ''), relation_time
            )
            
            if not source_exists:
                issues.append("源实体在关系时间点不存在")
                score = 0.5
            
            if not target_exists:
                issues.append("目标实体在关系时间点不存在")
                score = 0.5
            
            return {
                'score': score,
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"关系时序验证失败: {str(e)}")
            return {
                'score': 0.5,
                'issues': [f"时序验证异常: {str(e)}"]
            }
    
    async def _get_entity_type(self, entity_name: str) -> str:
        """获取实体类型"""
        try:
            # 从存储中查询实体类型
            entities = await self.store.search_entities(name=entity_name, limit=1)
            if entities and len(entities) > 0:
                return entities[0].get('type', 'unknown')
            return 'unknown'
        except Exception:
            return 'unknown'
    
    async def _check_entity_exists_at_time(self, entity_name: str, timestamp: Any) -> bool:
        """检查实体在指定时间是否存在"""
        # 简化实现，实际应该查询存储
        return True
    
    async def _group_similar_relations(
        self, 
        relations: List[Dict[str, Any]], 
        threshold: float
    ) -> List[List[Dict[str, Any]]]:
        """分组相似关系"""
        groups = []
        processed = set()
        
        for i, relation in enumerate(relations):
            if i in processed:
                continue
            
            current_group = [relation]
            processed.add(i)
            
            # 查找相似关系
            for j, other_relation in enumerate(relations[i+1:], i+1):
                if j in processed:
                    continue
                
                similarity = self._calculate_relation_similarity(relation, other_relation)
                if similarity >= threshold:
                    current_group.append(other_relation)
                    processed.add(j)
            
            if len(current_group) > 1:
                groups.append(current_group)
        
        return groups
    
    def _calculate_relation_similarity(
        self, 
        relation1: Dict[str, Any], 
        relation2: Dict[str, Any]
    ) -> float:
        """计算关系相似度"""
        # 基础相似度计算
        source_match = relation1.get('source_entity', '') == relation2.get('source_entity', '')
        target_match = relation1.get('target_entity', '') == relation2.get('target_entity', '')
        type_match = relation1.get('relation_type', '') == relation2.get('relation_type', '')
        
        # 计算相似度分数
        matches = sum([source_match, target_match, type_match])
        return matches / 3.0
    
    async def _merge_relations(
        self, 
        relations: List[Dict[str, Any]], 
        strategy: str
    ) -> Optional[Dict[str, Any]]:
        """合并关系"""
        if not relations:
            return None
        
        # 选择主关系（通常选择第一个或置信度最高的）
        primary_relation = relations[0]
        
        if strategy == "confidence_weighted":
            # 选择置信度最高的关系作为主关系
            max_confidence = 0
            for relation in relations:
                confidence = relation.get('properties', {}).get('confidence', 0)
                if confidence > max_confidence:
                    max_confidence = confidence
                    primary_relation = relation
        
        # 合并属性
        merged_properties = primary_relation.get('properties', {}).copy()
        
        # 更新置信度（取平均值或最大值）
        confidences = [r.get('properties', {}).get('confidence', 0) for r in relations]
        merged_properties['confidence'] = max(confidences) if confidences else 0
        merged_properties['merged_sources'] = [r.get('properties', {}).get('source', '') 
                                               for r in relations if r.get('properties', {}).get('source')]
        
        primary_relation['properties'] = merged_properties
        return primary_relation
    
    async def _calculate_relation_quality_scores(
        self, 
        relation: Dict[str, Any], 
        criteria: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """计算关系质量分数"""
        # 语义分数
        semantic_score = await self._calculate_semantic_score(relation)
        
        # 结构分数
        structural_score = await self._calculate_structural_score(relation)
        
        # 时序分数
        temporal_score = await self._calculate_temporal_score(relation)
        
        # 综合分数
        overall = (semantic_score + structural_score + temporal_score) / 3.0
        
        return {
            'overall': overall,
            'semantic': semantic_score,
            'structural': structural_score,
            'temporal': temporal_score
        }
    
    async def _calculate_semantic_score(self, relation: Dict[str, Any]) -> float:
        """计算语义分数"""
        try:
            # 使用语义验证逻辑
            semantic_validation = await self._validate_relation_semantics(relation)
            return semantic_validation['score']
        except Exception:
            return 0.5
    
    async def _calculate_structural_score(self, relation: Dict[str, Any]) -> float:
        """计算结构分数"""
        try:
            # 使用结构验证逻辑
            structural_validation = await self._validate_relation_structure(relation)
            return structural_validation['score']
        except Exception:
            return 0.5
    
    async def _calculate_temporal_score(self, relation: Dict[str, Any]) -> float:
        """计算时序分数"""
        try:
            # 使用时序验证逻辑
            temporal_validation = await self._validate_relation_temporal(relation)
            return temporal_validation['score']
        except Exception:
            return 0.5
    
    async def _identify_relation_quality_issues(
        self, 
        relation: Dict[str, Any], 
        quality_scores: Dict[str, float]
    ) -> List[str]:
        """识别关系质量问题"""
        issues = []
        
        if quality_scores['semantic'] < 0.7:
            issues.append("关系语义不一致")
        
        if quality_scores['structural'] < 0.8:
            issues.append("关系结构不完整")
        
        if quality_scores['temporal'] < 0.8:
            issues.append("关系时序不合理")
        
        return issues
    
    async def _generate_relation_quality_suggestions(
        self, 
        relation: Dict[str, Any], 
        issues: List[str]
    ) -> List[str]:
        """生成关系质量改进建议"""
        suggestions = []
        
        for issue in issues:
            if "语义" in issue:
                suggestions.append("检查关系类型与实体类型的语义一致性")
            elif "结构" in issue:
                suggestions.append("补充关系的置信度和来源信息")
            elif "时序" in issue:
                suggestions.append("验证关系时间点的合理性")
        
        return suggestions
    
    async def _get_all_relations(self) -> List[Dict[str, Any]]:
        """获取所有关系"""
        # 这里可以实现具体的查询逻辑
        # 目前返回空列表，需要从存储中获取
        return []
    
    async def _execute_relation_cleanup(self, invalid_relations: List[Dict[str, Any]]) -> Dict[str, int]:
        """执行关系清理"""
        stats = {
            'removed': 0,
            'updated': 0
        }
        
        for item in invalid_relations:
            relation = item['relation']
            validation_result = item['validation_result']
            
            # 根据验证结果决定清理策略
            if validation_result.validation_score < 0.3:
                # 低质量关系，直接移除
                # await self.store.remove_relation(relation.get('id'))
                stats['removed'] += 1
            elif validation_result.validation_score < 0.6:
                # 中等质量关系，标记待审核
                # await self.store.update_relation_status(relation.get('id'), 'pending_review')
                stats['updated'] += 1
        
        return stats