"""
实体关系判断模块 - 基于大模型prompt的多实体语义关联分析
"""
from typing import List, Optional

from app.core.base_service import BaseService
from app.core.models import (
    Entity,
    EntityResolutionResult,
    EntityComparisonResult,
    SimilarEntityResult
)
from app.llm.llm_service import LLMService
from app.utils.json_extractor import extract_json_robust
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class EntityAnalyzer(BaseService):
    """实体分析服务，提供实体关系判断和语义关联分析功能"""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """初始化实体分析器"""
        super().__init__(llm_service=llm_service)
        logger.info("初始化 EntityAnalyzer")
    
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
                context=f"类型: {entity.type}, 描述: {entity.description}",
                candidate_descriptions='\n'.join(candidates_info)
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
    
    
    def _parse_entity_resolution_response(
        self, 
        response: str, 
        candidate_entities: List[Entity]
    ) -> EntityResolutionResult:
        """解析实体消歧响应（使用json_extractor模块）
        
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
            data = extract_json_robust(response)
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
        """解析多实体比较响应（使用json_extractor模块）
        
        Args:
            response: 大模型响应文本
            
        Returns:
            List[EntityComparisonResult]: 解析后的实体比较结果列表
            
        Raises:
            ValueError: 当响应格式无效时
        """
        try:
            # 使用统一的JSON提取方法
            result = extract_json_robust(response)
            
            if not result:
                logger.warning("未能从响应中提取有效的JSON数据")
                return []
            
            # 处理数组或包含数组的对象
            if isinstance(result, list):
                data = result
            elif isinstance(result, dict) and 'items' in result:
                data = result['items']
            elif isinstance(result, dict) and 'comparisons' in result:
                data = result['comparisons']
            else:
                logger.warning(f"提取的结果不是数组类型: {type(result)}")
                return []
            
            comparisons = []
            for item_data in data:
                try:
                    # 验证必需字段
                    required_fields = ['entity1', 'entity2', 'similarity', 'is_same_entity', 'reasoning']
                    if not self.validate_response_data(item_data, required_fields):
                        continue
                    
                    # 构建实体对象
                    entity1 = Entity(
                        name=item_data.get('entity1', ''),
                        type=item_data.get('entity1_type', ''),
                        description=item_data.get('entity1_description', '')
                    )
                    
                    entity2 = Entity(
                        name=item_data.get('entity2', ''),
                        type=item_data.get('entity2_type', ''),
                        description=item_data.get('entity2_description', '')
                    )
                    
                    comparisons.append(EntityComparisonResult(
                        entity1=entity1,
                        entity2=entity2,
                        similarity_score=item_data.get('similarity', 0.0),
                        is_same_entity=item_data.get('is_same_entity', False),
                        reasoning=item_data.get('reasoning', '')
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