"""
实体关系判断模块 - 基于大模型prompt的多实体语义关联分析
"""
import logging
from typing import List, Optional

from app.core.base_service import BaseService
from app.core.models import (
    Entity,
    EntityResolutionResult,
    EntityComparisonResult,
    SimilarEntityResult
)

logger = logging.getLogger(__name__)


class EntityAnalyzer(BaseService):
    """实体分析服务，提供实体关系判断和语义关联分析功能"""
    
    async def resolve_entity_ambiguity(
        self, 
        entity: Entity, 
        candidate_entities: List[Entity]
    ) -> EntityResolutionResult:
        """解决实体消歧问题，从候选实体中选择最匹配的一个
        
        Args:
            entity: 需要消歧的目标实体
            candidate_entities: 候选实体列表
            
        Returns:
            EntityResolutionResult: 实体消歧结果
            
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当LLM调用失败时
        """
        try:
            if not entity:
                raise ValueError("目标实体不能为空")
            
            if not candidate_entities:
                return EntityResolutionResult(
                    selected_entity=None,
                    confidence=0.0,
                    reasoning="没有提供候选实体"
                )
            
            logger.info(f"开始实体消歧，目标实体: {entity.name}, 候选实体数: {len(candidate_entities)}")
            
            # 构建候选实体信息
            candidates_info = []
            for candidate in candidate_entities:
                info = f"名称: {candidate.name}, 类型: {candidate.type}, 描述: {candidate.description}"
                if hasattr(candidate, 'properties') and candidate.properties:
                    info += f", 属性: {candidate.properties}"
                candidates_info.append(info)
            
            # 使用大模型进行实体消歧
            response = await self.generate_with_prompt(
                'entity_resolution',
                entity_name=entity.name,
                entity_context=f"类型: {entity.type}, 描述: {entity.description}",
                candidate_entities='\n'.join(candidates_info)
            )
            
            # 解析响应
            return self._parse_entity_resolution_response(response, candidate_entities)
            
        except Exception as e:
            logger.error(f"实体消歧失败: {e}")
            raise RuntimeError(f"实体消歧失败: {str(e)}")
    
    async def compare_entities(self, entities: List[Entity]) -> List[EntityComparisonResult]:
        """比较多个实体之间的语义相似性
        
        Args:
            entities: 实体列表（长度必须 >= 2）
            
        Returns:
            List[EntityComparisonResult]: 实体比较结果列表
            
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当LLM调用失败时
        """
        try:
            if len(entities) < 2:
                raise ValueError("实体列表必须包含至少2个实体")
            
            logger.info(f"开始实体比较，实体数: {len(entities)}")
            
            # 构建实体信息
            entities_info = []
            for entity in entities:
                info = f"名称: {entity.name}, 类型: {entity.type}, 描述: {entity.description}"
                if hasattr(entity, 'properties') and entity.properties:
                    info += f", 属性: {entity.properties}"
                entities_info.append(info)
            
            # 使用大模型进行实体比较
            response = await self.generate_with_prompt(
                'multi_entity_comparison',
                entities_info='\n'.join(entities_info)
            )
            
            # 解析响应
            return self._parse_multi_entity_comparison_response(response)
            
        except Exception as e:
            logger.error(f"实体比较失败: {e}")
            raise RuntimeError(f"实体比较失败: {str(e)}")
    
    async def find_similar_entities(
        self,
        target_entity: Entity,
        candidate_entities: List[Entity],
        similarity_threshold: float = 0.7
    ) -> List[SimilarEntityResult]:
        """从候选实体中查找与目标实体相似的实体
        
        Args:
            target_entity: 目标实体
            candidate_entities: 候选实体列表
            similarity_threshold: 相似度阈值（默认0.7）
            
        Returns:
            List[SimilarEntityResult]: 相似实体结果列表，按相似度降序排列
            
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当LLM调用失败时
        """
        try:
            if not target_entity:
                raise ValueError("目标实体不能为空")
            
            if not candidate_entities:
                return []
            
            if not 0.0 <= similarity_threshold <= 1.0:
                raise ValueError("相似度阈值必须在0.0-1.0之间")
            
            logger.info(f"开始查找相似实体，目标: {target_entity.name}, 候选数: {len(candidate_entities)}")
            
            # 使用实体比较功能
            all_entities = [target_entity] + candidate_entities
            comparison_results = await self.compare_entities(all_entities)
            
            # 提取与目标实体相关的比较结果
            similar_entities = []
            for result in comparison_results:
                if (result.entity1.name == target_entity.name and 
                    result.is_same_entity and 
                    result.similarity_score >= similarity_threshold):
                    # 找到对应的候选实体
                    candidate = next(
                        (e for e in candidate_entities if e.name == result.entity2.name), 
                        None
                    )
                    if candidate:
                        similar_entities.append(SimilarEntityResult(
                            entity=candidate,
                            similarity_score=result.similarity_score,
                            reasoning=result.reasoning
                        ))
                elif (result.entity2.name == target_entity.name and 
                      result.is_same_entity and 
                      result.similarity_score >= similarity_threshold):
                    # 找到对应的候选实体
                    candidate = next(
                        (e for e in candidate_entities if e.name == result.entity1.name), 
                        None
                    )
                    if candidate:
                        similar_entities.append(SimilarEntityResult(
                            entity=candidate,
                            similarity_score=result.similarity_score,
                            reasoning=result.reasoning
                        ))
            
            # 按相似度降序排列
            similar_entities.sort(key=lambda x: x.similarity_score, reverse=True)
            
            logger.info(f"相似实体查找完成，找到 {len(similar_entities)} 个相似实体")
            return similar_entities
            
        except Exception as e:
            logger.error(f"查找相似实体失败: {e}")
            raise RuntimeError(f"查找相似实体失败: {str(e)}")
    
    def _parse_entity_resolution_response(
        self, 
        response: str, 
        candidate_entities: List[Entity]
    ) -> EntityResolutionResult:
        """解析实体消歧响应
        
        Args:
            response: 大模型响应文本
            candidate_entities: 候选实体列表
            
        Returns:
            EntityResolutionResult: 解析后的实体消歧结果
            
        Raises:
            ValueError: 当响应格式无效时
        """
        try:
            # 提取JSON数据
            data = self.extract_json_from_response(response)
            if not data:
                raise ValueError("无法从响应中提取有效数据")
            
            # 验证必需字段
            required_fields = ['selected_entity', 'confidence', 'reasoning']
            if not self.validate_response_data(data, required_fields):
                raise ValueError("响应缺少必需字段")
            
            # 解析选中的实体
            selected_entity = None
            selected_name = data.get('selected_entity', '').strip()
            
            if selected_name:
                # 从候选实体中找到匹配的实体
                selected_entity = next(
                    (entity for entity in candidate_entities 
                     if entity.name == selected_name), 
                    None
                )
                
                # 如果没找到完全匹配的，尝试模糊匹配
                if not selected_entity:
                    selected_entity = next(
                        (entity for entity in candidate_entities 
                         if selected_name in entity.name or entity.name in selected_name), 
                        None
                    )
            
            return EntityResolutionResult(
                selected_entity=selected_entity,
                confidence=data.get('confidence', 0.0),
                reasoning=data.get('reasoning', '')
            )
            
        except Exception as e:
            logger.error(f"解析实体消歧响应失败: {e}")
            raise ValueError(f"解析实体消歧响应失败: {str(e)}")
    
    def _parse_multi_entity_comparison_response(
        self, 
        response: str
    ) -> List[EntityComparisonResult]:
        """解析多实体比较响应
        
        Args:
            response: 大模型响应文本
            
        Returns:
            List[EntityComparisonResult]: 解析后的实体比较结果列表
            
        Raises:
            ValueError: 当响应格式无效时
        """
        try:
            # 提取JSON数组数据
            results_data = self.extract_json_array_from_response(response)
            if not results_data:
                raise ValueError("无法从响应中提取有效数据")
            
            comparisons = []
            for data in results_data:
                try:
                    # 验证必需字段
                    required_fields = ['entity1', 'entity2', 'similarity', 'is_same_entity', 'reasoning']
                    if not self.validate_response_data(data, required_fields):
                        continue
                    
                    # 构建实体对象
                    entity1 = Entity(
                        name=data.get('entity1', ''),
                        type=data.get('entity1_type', ''),
                        description=data.get('entity1_description', '')
                    )
                    
                    entity2 = Entity(
                        name=data.get('entity2', ''),
                        type=data.get('entity2_type', ''),
                        description=data.get('entity2_description', '')
                    )
                    
                    comparisons.append(EntityComparisonResult(
                        entity1=entity1,
                        entity2=entity2,
                        similarity_score=data.get('similarity', 0.0),
                        is_same_entity=data.get('is_same_entity', False),
                        reasoning=data.get('reasoning', '')
                    ))
                    
                except Exception as e:
                    logger.warning(f"解析单个比较结果失败: {e}")
                    continue
            
            if not comparisons:
                raise ValueError("未找到有效的比较结果")
            
            return comparisons
            
        except Exception as e:
            logger.error(f"解析多实体比较响应失败: {e}")
            raise ValueError(f"解析多实体比较响应失败: {str(e)}")
    
    def parse_llm_response(self, response: str) -> dict:
        """实现基础类的抽象方法
        
        Args:
            response: 大模型响应文本
            
        Returns:
            dict: 空字典，实体分析器使用专门的解析方法
        """
        # 实体分析器有专门的解析方法，这里返回空字典
        return {}