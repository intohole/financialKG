"""
内容处理模块 - 基于大模型prompt的内容分类和实体关系提取

功能：
- 内容分类：判断文本所属类别（金融、科技、医疗等）
- 实体关系提取：从文本中提取实体及其相互关系

使用示例：
    processor = ContentProcessor()
    
    # 内容分类
    classification = await processor.classify_content("苹果公司发布了新款iPhone")
    
    # 实体关系提取
    extraction = await processor.extract_entities_and_relations("苹果公司发布了新款iPhone")
"""
from typing import List, Optional, Dict

from app.config.config_manager import CategoryConfigItem
from app.core.base_service import BaseService
from app.core.extract_models import (
    ContentClassification,
    ContentClassificationResult,
    Entity,
    KnowledgeExtractionResult,
    KnowledgeGraph,
    Relation
)
from app.core.prompt_parameter_builder import (
    PromptParameterBuilder,
    CompositeParameterBuilder
)
from app.llm.llm_service import LLMService
from app.utils.json_extractor import extract_json_robust

from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ContentProcessor(BaseService):
    """
    内容处理服务，提供内容分类和实体关系提取功能
    
    主要方法：
    - classify_content: 对输入文本进行内容分类
    - extract_entities_and_relations: 从文本中提取实体及其相互关系
    """
    
    def __init__(self, parameter_builder: Optional[PromptParameterBuilder] = None, llm_service: Optional[LLMService] = None):
        """
        初始化内容处理器
        
        Args:
            parameter_builder: 可选的自定义参数构建器，默认为CompositeParameterBuilder
            llm_service: 可选的自定义LLM服务，默认为None
        """
        super().__init__(llm_service=llm_service)
        self.parameter_builder = parameter_builder or CompositeParameterBuilder()
        logger.info(f"初始化 ContentProcessor，使用参数构建器: {self.parameter_builder.__class__.__name__}")
    
    async def classify_content(self, text: str,
                             categories: Optional[List[str]] = None,
                             categories_prompt :str =None,
                             category_config: Optional[CategoryConfigItem] = None,
                             prompt_key: Optional[str] = None) -> ContentClassificationResult:
        """
        对文本内容进行分类，判断其所属类别
        
        Args:
            text: 待分类的文本内容
            categories: 可选的类别列表，如不提供则使用默认类别
            categories_prompt:
            category_config: 可选的类别配置字典，包含名称、描述、实体类型、关系类型
            prompt_key: 使用的prompt键名，默认为'content_classification'，可自定义
            
        Returns:
            ContentClassificationResult: 分类结果，包含类别、置信度和理由
            
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当LLM调用失败时
        """
        # 参数验证 - 在try块之外，以便直接抛出ValueError
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
            
        try:
            logger.info(f"开始内容分类，文本长度: {len(text)}")
            
            if prompt_key is None:
                prompt_key = 'content_classification_enhanced'

            
            # 使用参数构建器构建提示词参数
            prompt_params = self.parameter_builder.build_parameters(
                text=text,
                prompt_key=prompt_key,
                categories=categories,
                categories_prompt=categories_prompt,
                category_config=category_config
            )
            
            # 使用大模型进行内容分类
            response = await self.generate_with_prompt(prompt_key, **prompt_params)
            
            # 解析响应
            return self._parse_classification_response(response, text)
            
        except Exception as e:
            logger.error(f"内容分类失败: {e}")
            raise RuntimeError(f"内容分类失败: {str(e)}")
    
    async def extract_entities_and_relations(self, 
                                           text: str,
                                           entity_types: Optional[List[str]] = None,
                                           relation_types: Optional[List[str]] = None,
                                           prompt_key: Optional[str] = None,
                                           current_category: str = 'financial') -> KnowledgeExtractionResult:
        """
        从文本中提取实体及其相互关系 - 统一版本
        
        Args:
            text: 待提取的文本内容
            entity_types: 可选的实体类型列表，如不提供则使用默认类型
            relation_types: 可选的关系类型列表，如不提供则使用默认类型
            prompt_key: 使用的prompt键名，默认为'entity_relation_extraction_unified'
            category_config: 类别配置字典，用于动态实体和关系类型
            current_category: 当前类别，用于选择对应的配置
            
        Returns:
            KnowledgeExtractionResult: 实体关系提取结果，包含实体列表和关系列表
            
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当LLM调用失败时
        """
        # 参数验证 - 在try块之外，以便直接抛出ValueError
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
            
        try:
            logger.info(f"开始实体关系提取，文本长度: {len(text)}")
            
            # 自动选择提示词：默认使用统一版本，除非明确指定其他类型
            if prompt_key is None:
                prompt_key = 'entity_relation_extraction_unified'
            
            # 记录参数构建的详细信息，便于问题排查
            logger.info(f"实体关系提取参数 - prompt_key: {prompt_key}, "
                       f"entity_types: {entity_types}, relation_types: {relation_types}, "
                       f"current_category: {current_category}")
            
            # 使用参数构建器构建提示词参数
            prompt_params = self.parameter_builder.build_parameters(
                text=text,
                prompt_key=prompt_key,
                entity_types=entity_types,
                relation_types=relation_types
            )
            
            logger.info(f"构建的提示词参数 - entity_types: {prompt_params.get('entity_types', 'N/A')}, "
                       f"relation_types: {prompt_params.get('relation_types', 'N/A')}")
            
            # 使用大模型进行实体关系提取
            response = await self.generate_with_prompt(prompt_key, **prompt_params)
            
            # 解析响应
            result = self._parse_extraction_response(response, text)
            
            logger.info(f"实体关系提取完成 - 实体数量: {len(result.knowledge_graph.entities)}, "
                       f"关系数量: {len(result.knowledge_graph.relations)}")
            
            return result
            
        except Exception as e:
            logger.error(f"实体关系提取失败: {e}", exc_info=True)
            
            # 添加详细的错误追踪信息
            logger.error("实体关系提取失败详情:")
            logger.error(f"- prompt_key: {prompt_key}")
            logger.error(f"- 文本长度: {len(text) if text else 0}")
            logger.error(f"- entity_types: {entity_types}")
            logger.error(f"- relation_types: {relation_types}")
            logger.error(f"- category_config: {bool(category_config)}")
            logger.error(f"- current_category: {current_category}")
            
            raise RuntimeError(f"实体关系提取失败: {str(e)}")
    
    def _parse_classification_response(self, response: str, original_text: str = "") -> ContentClassificationResult:
        """统一JSON格式解析分类响应（使用json_extractor模块）"""
        try:
            # 提取JSON数据
            data = extract_json_robust(response)
            if not data:
                raise ValueError("无法从响应中提取有效JSON数据")
            
            # 验证必需字段
            required_fields = ['category']
            if not self.validate_response_data(data, required_fields):
                raise ValueError(f"响应缺少必需字段: {required_fields}")
            
            # 解析分类结果
            category_str = str(data.get('category', 'UNKNOWN')).lower()
            
            return ContentClassificationResult(
                category=category_str,
                confidence=float(data.get('confidence', 1.)),
                reasoning=str(data.get('reasoning', '')),
                supported=bool(data.get('supported', True))
            )
            
        except Exception as e:
            logger.error(f"解析分类响应失败: {e}")
            raise ValueError(f"解析分类响应失败: {str(e)}")
    
    def _parse_text_classification_response(self, response: str, original_text: str = "") -> ContentClassificationResult:
        """已废弃 - 统一使用JSON格式解析"""
        raise ValueError("文本格式解析已废弃，所有响应必须使用JSON格式")
    
    def _parse_extraction_response(self, response: str, original_text: str = "") -> KnowledgeExtractionResult:
        """统一JSON格式解析实体关系提取响应（使用json_extractor模块）"""
        try:
            # 提取JSON数据
            data = extract_json_robust(response)
            if not data:
                raise ValueError("无法从响应中提取有效JSON数据")
            
            # 验证必需字段
            required_fields = ['is_financial_content', 'confidence']
            if not self.validate_response_data(data, required_fields):
                raise ValueError(f"响应缺少必需字段: {required_fields}")
            
            # 解析实体列表
            entities = []
            for entity_data in data.get('entities', []):
                try:
                    entity = Entity(
                        name=str(entity_data.get('name', '')),
                        type=str(entity_data.get('type', '')),
                        description=str(entity_data.get('description', ''))
                    )
                    if entity.name:  # 只添加非空实体
                        entities.append(entity)
                except Exception as e:
                    logger.warning(f"解析实体失败: {e}")
            
            # 解析关系列表
            relations = []
            for relation_data in data.get('relations', []):
                try:
                    # 兼容不同的字段命名格式
                    subject = str(relation_data.get('subject', relation_data.get('source', '')))
                    predicate = str(relation_data.get('predicate', relation_data.get('relation_type', '')))
                    object_entity = str(relation_data.get('object', relation_data.get('target', '')))
                    
                    if subject and predicate and object_entity:  # 只添加完整关系
                        relation = Relation(
                            subject=subject,
                            predicate=predicate,
                            object=object_entity,
                            description=str(relation_data.get('description', '')),
                            confidence=float(relation_data.get('confidence', 0.0))
                        )
                        relations.append(relation)
                except Exception as e:
                    logger.warning(f"解析关系失败: {e}")
            
            # 创建结果对象
            content_classification = ContentClassification(
                confidence=float(data.get('confidence', 0.0)),
                category=data.get('category'),
                reasoning=data.get('reasoning')
            )
            
            knowledge_graph = KnowledgeGraph(
                entities=entities,
                relations=relations,
                category=data.get('category'),
                metadata=data.get('metadata', {})
            )
            
            return KnowledgeExtractionResult(
                content_classification=content_classification,
                knowledge_graph=knowledge_graph,
                raw_text=original_text
            )
            
        except Exception as e:
            logger.error(f"解析提取响应失败: {e}")
            raise ValueError(f"解析提取响应失败: {str(e)}")
    
    def parse_llm_response(self, response: str) -> dict:
        """实现基础类的抽象方法"""
        # 内容处理器有专门的解析方法，这里返回空字典
        return {}