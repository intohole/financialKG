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
    ContentClassificationResult,
    Entity,
    KnowledgeExtractionResult,
    Relation
)

logger = logging.getLogger(__name__)


class ContentProcessor(BaseService):
    """
    内容处理服务，提供内容分类和实体关系提取功能
    
    主要方法：
    - classify_content: 对输入文本进行内容分类
    - extract_entities_and_relations: 从文本中提取实体及其相互关系
    """
    
    async def classify_content(self, text: str, categories: Optional[List[str]] = None, 
                             category_config: Optional[Dict[str, Dict]] = None,
                             prompt_key: str = 'content_classification') -> ContentClassificationResult:
        """
        对输入文本进行内容分类
        
        Args:
            text: 待分类的文本内容
            categories: 可选的类别列表，如不提供则使用默认类别
            category_config: 可选的类别配置，包含每个类别的详细信息
            prompt_key: 使用的prompt键名，默认为'content_classification'，可自定义
            
        Returns:
            ContentClassificationResult: 内容分类结果，包含类别、置信度等信息
            
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当LLM调用失败时
        """
        try:
            if not text or not text.strip():
                raise ValueError("文本内容不能为空")
            
            logger.info(f"开始内容分类，文本长度: {len(text)}")
            
            # 构建类别信息
            if categories:
                category_info = ", ".join(categories)
            elif category_config:
                # 使用配置中的类别信息，包含名称和描述
                category_info_parts = []
                for category_key, category_data in category_config.items():
                    name = category_data.get('name', category_key)
                    description = category_data.get('description', '')
                    category_info_parts.append(f"{category_key}({name}): {description}")
                category_info = "; ".join(category_info_parts)
            else:
                category_info = "financial(金融财经): 金融、财经、股票、证券等相关内容; technology(科技互联网): 科技、互联网、人工智能等相关内容; medical(医疗健康): 医疗、健康、药品、生物科技等相关内容; education(教育培训): 教育、培训、学术等相关内容"
            
            # 使用大模型进行内容分类
            response = await self.generate_with_prompt(
                prompt_key,
                text=text,
                categories=category_info
            )
            
            # 解析响应
            return self._parse_classification_response(response, text)
            
        except Exception as e:
            logger.error(f"内容分类失败: {e}")
            raise RuntimeError(f"内容分类失败: {str(e)}")
    
    async def extract_entities_and_relations(self, text: str, 
                                           entity_types: Optional[List[str]] = None,
                                           relation_types: Optional[List[str]] = None,
                                           prompt_key: str = 'entity_relation_extraction') -> KnowledgeExtractionResult:
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
        try:
            if not text or not text.strip():
                raise ValueError("文本内容不能为空")
            
            logger.info(f"开始实体关系提取，文本长度: {len(text)}")
            
            # 构建实体类型和关系类型信息
            entity_types_info = ", ".join(entity_types) if entity_types else "公司/企业, 人物, 产品/服务, 地点, 事件, 概念/术语"
            relation_types_info = ", ".join(relation_types) if relation_types else "属于/子公司, 投资/收购, 合作/竞争, 位于, 参与, 影响"
            
            # 使用大模型进行实体关系提取
            response = await self.generate_with_prompt(
                prompt_key,
                text=text,
                entity_types=entity_types_info,
                relation_types=relation_types_info
            )
            
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
            # 提取JSON数据
            data = self.extract_json_from_response(response)
            if not data:
                raise ValueError("无法从响应中提取有效数据")
            
            # 验证必需字段
            required_fields = ['category', 'confidence', 'reasoning']
            if not self.validate_response_data(data, required_fields):
                raise ValueError("响应缺少必需字段")
            
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
            
        except Exception as e:
            logger.error(f"解析分类响应失败: {e}")
            raise ValueError(f"解析分类响应失败: {str(e)}")
    
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
                        description=entity_data.get('description', ''),
                        properties=entity_data.get('properties', {})
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
                    relation = Relation(
                        source_entity=relation_data.get('source', ''),
                        target_entity=relation_data.get('target', ''),
                        relation_type=relation_data.get('relation_type', ''),
                        confidence=relation_data.get('confidence', 0.0),
                        description=relation_data.get('description', ''),
                        properties=relation_data.get('properties', {})
                    )
                    relations.append(relation)
                except Exception as e:
                    logger.warning(f"解析关系失败: {e}")
                    continue
            
            return KnowledgeExtractionResult(
                is_financial_content=data.get('is_financial_content', False),
                confidence=data.get('confidence', 0.0),
                entities=entities,
                relations=relations
            )
            
        except Exception as e:
            logger.error(f"解析提取响应失败: {e}")
            raise ValueError(f"解析提取响应失败: {str(e)}")
    
    def parse_llm_response(self, response: str) -> dict:
        """实现基础类的抽象方法"""
        # 内容处理器有专门的解析方法，这里返回空字典
        return {}