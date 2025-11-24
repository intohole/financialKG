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
import logging
from typing import List, Optional, Dict

from app.core.base_service import BaseService
from app.core.models import (
    ContentCategory,
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

logger = logging.getLogger(__name__)


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
                             category_config: Optional[Dict[str, Dict]] = None,
                             prompt_key: Optional[str] = None) -> ContentClassificationResult:
        """
        对文本内容进行分类，判断其所属类别
        
        Args:
            text: 待分类的文本内容
            categories: 可选的类别列表，如不提供则使用默认类别
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
            
            # 自动选择提示词：如果提供了自定义类别或配置，使用 content_classification_enhanced，否则使用默认的 content_classification
            if prompt_key is None:
                prompt_key = 'content_classification'
            
            # 使用参数构建器构建提示词参数
            prompt_params = self.parameter_builder.build_parameters(
                text=text,
                prompt_key=prompt_key,
                categories=categories,
                category_config=category_config
            )
            
            # 使用大模型进行内容分类
            response = await self.generate_with_prompt(prompt_key, **prompt_params)
            
            # 解析响应
            return self._parse_classification_response(response, text)
            
        except Exception as e:
            logger.error(f"内容分类失败: {e}")
            raise RuntimeError(f"内容分类失败: {str(e)}")
    
    async def extract_entities_and_relations(self, text: str, 
                                           entity_types: Optional[List[str]] = None,
                                           relation_types: Optional[List[str]] = None,
                                           prompt_key: Optional[str] = None) -> KnowledgeExtractionResult:
        """
        从文本中提取实体及其相互关系
        
        Args:
            text: 待提取的文本内容
            entity_types: 可选的实体类型列表，如不提供则使用默认类型
            relation_types: 可选的关系类型列表，如不提供则使用默认类型
            prompt_key: 使用的prompt键名，默认为'entity_relation_extraction'，可自定义
            
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
            
            # 自动选择提示词：默认使用 entity_relation_extraction，除非明确指定其他类型
            if prompt_key is None:
                prompt_key = 'entity_relation_extraction'
            
            # 使用参数构建器构建提示词参数
            prompt_params = self.parameter_builder.build_parameters(
                text=text,
                prompt_key=prompt_key,
                entity_types=entity_types,
                relation_types=relation_types
            )
            
            # 使用大模型进行实体关系提取
            response = await self.generate_with_prompt(prompt_key, **prompt_params)
            
            # 解析响应
            return self._parse_extraction_response(response, text)
            
        except Exception as e:
            logger.error(f"实体关系提取失败: {e}")
            raise RuntimeError(f"实体关系提取失败: {str(e)}")
    
    def _parse_classification_response(self, response: str, original_text: str = "") -> ContentClassificationResult:
        """
        解析内容分类响应
        
        Args:
            response: 大模型响应文本
            original_text: 原始输入文本（可选）
            
        Returns:
            ContentClassificationResult: 解析后的分类结果
            
        Raises:
            ValueError: 当响应格式无效时
        """
        try:
            # 首先尝试提取JSON数据
            data = self.extract_json_from_response(response)
            if data:
                # JSON格式解析
                required_fields = ['category', 'confidence', 'reasoning']
                if not self.validate_response_data(data, required_fields):
                    raise ValueError("响应   缺少必需字段")
                
                # 解析分类结果
                category_str = data.get('category', 'UNKNOWN')
                try:
                    category = ContentCategory(category_str)
                except ValueError:
                    category = ContentCategory.UNKNOWN
                
                return ContentClassificationResult(
                    category=category,
                    confidence=data.get('confidence', 0.0),
                    reasoning=data.get('reasoning', ''),
                    is_financial_content=data.get('is_financial_content', False),
                    supported=data.get('supported', True)
                )
            
            # 如果不是JSON格式，抛出异常（现在所有prompt都要求JSON格式）
            raise ValueError("响应格式不是有效的JSON格式")
            
        except Exception as e:
            logger.error(f"解析分类响应失败: {e}")
            raise ValueError(f"解析分类响应失败: {str(e)}")
    
    def _parse_text_classification_response(self, response: str, original_text: str = "") -> ContentClassificationResult:
        """
        解析文本格式的分类响应（已废弃，保留方法签名用于兼容性）
        
        Args:
            response: 大模型响应文本
            original_text: 原始输入文本（可选）
            
        Returns:
            ContentClassificationResult: 解析后的分类结果
            
        Raises:
            ValueError: 当响应格式无效时（现在总是抛出异常）
        """
        # 现在所有prompt都要求JSON格式，文本解析已废弃
        raise ValueError("文本格式解析已废弃，请使用JSON格式响应")
    
    def _parse_extraction_response(self, response: str, original_text: str = "") -> KnowledgeExtractionResult:
        """
        解析实体关系提取响应
        
        Args:
            response: 大模型响应文本
            original_text: 原始输入文本（可选）
            
        Returns:
            KnowledgeExtractionResult: 解析后的提取结果
            
        Raises:
            ValueError: 当响应格式无效时
        """
        try:
            # 提取JSON数据
            data = self.extract_json_from_response(response)
            if not data:
                raise ValueError("无法从响应中提取有效数据")
            
            # 验证必需字段
            required_fields = ['is_financial_content', 'confidence']
            if not self.validate_response_data(data, required_fields):
                raise ValueError("响应缺少必需字段")
            
            # 解析实体列表
            entities = []
            entities_data = data.get('entities', [])
            for entity_data in entities_data:
                try:
                    entity = Entity(
                        name=entity_data.get('name', ''),
                        type=entity_data.get('type', ''),
                        description=entity_data.get('description', '')
                    )
                    entities.append(entity)
                except Exception as e:
                    logger.warning(f"解析实体失败: {e}")
                    continue
            
            # 解析关系列表
            relations = []
            relations_data = data.get('relations', [])
            for relation_data in relations_data:
                try:
                    # 兼容不同的字段命名格式
                    subject = relation_data.get('subject', relation_data.get('source', ''))
                    predicate = relation_data.get('predicate', relation_data.get('relation_type', ''))
                    object_entity = relation_data.get('object', relation_data.get('target', ''))
                    
                    relation = Relation(
                        subject=subject,
                        predicate=predicate,
                        object=object_entity,
                        description=relation_data.get('description', ''),
                        confidence=relation_data.get('confidence', 0.0)
                    )
                    relations.append(relation)
                except Exception as e:
                    logger.warning(f"解析关系失败: {e}")
                    continue
            
            # 创建内容分类结果
            content_classification = ContentClassification(
                is_financial_content=data.get('is_financial_content', False),
                confidence=data.get('confidence', 0.0),
                category=data.get('category'),
                reasoning=data.get('reasoning')
            )
            
            # 创建知识图谱
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