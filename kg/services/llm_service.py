"""
基于LangChain的大模型服务主类
整合所有LLM功能，提供统一的接口
"""
from typing import Dict, Any, List, Optional
import logging

from .llm.langchain_config import LangChainConfig
from .llm.entity_extraction import EntityExtractionService
from .llm.relation_extraction import RelationExtractionService
from .llm.news_summarization import NewsSummarizationService
from .llm.entity_aggregation import EntityAggregationService
from .llm.relation_aggregation import RelationAggregationService

logger = logging.getLogger(__name__)


class LLMService:
    """基于LangChain的大模型服务主类"""
    
    def __init__(self, config: Optional[LangChainConfig] = None):
        """
        初始化LLM服务
        
        Args:
            config: LangChain配置对象，如果不提供则使用默认配置
        """
        self.config = config or LangChainConfig()
        
        # 初始化各个服务
        self.entity_extraction = EntityExtractionService(self.config)
        self.relation_extraction = RelationExtractionService(self.config)
        self.news_summarization = NewsSummarizationService(self.config)
        self.entity_aggregation = EntityAggregationService(self.config)
        self.relation_aggregation = RelationAggregationService(self.config)
        
        logger.info("LLM服务初始化完成")
    
    async def extract_entities(self, text: str, entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        从文本中抽取实体
        
        Args:
            text: 输入文本
            entity_types: 要抽取的实体类型列表，如果不提供则抽取所有类型
            
        Returns:
            包含抽取结果的字典
        """
        logger.info(f"开始从文本中抽取实体，文本长度: {len(text)}")
        
        if entity_types:
            result = await self.entity_extraction.extract_entities_by_type(text, entity_types)
        else:
            result = await self.entity_extraction.extract_entities(text)
            
        logger.info(f"实体抽取完成，共抽取到 {len(result.get('entities', []))} 个实体")
        return result
    
    async def extract_relations(self, text: str, entities: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        从文本中抽取关系
        
        Args:
            text: 输入文本
            entities: 已知实体列表，如果不提供则先抽取实体
            
        Returns:
            包含抽取结果的字典
        """
        logger.info(f"开始从文本中抽取关系，文本长度: {len(text)}")
        
        if entities:
            result = await self.relation_extraction.extract_relations_with_entities(text, entities)
        else:
            result = await self.relation_extraction.extract_relations(text)
            
        logger.info(f"关系抽取完成，共抽取到 {len(result.get('relations', []))} 个关系")
        return result
    
    async def generate_news_summary(self, text: str, summary_type: str = "standard", **kwargs) -> Dict[str, Any]:
        """
        生成新闻摘要
        
        Args:
            text: 新闻文本
            summary_type: 摘要类型，可选值：standard, short, topic, multi_view
            **kwargs: 其他参数，根据摘要类型不同而不同
            
        Returns:
            包含摘要结果的字典
        """
        logger.info(f"开始生成新闻摘要，摘要类型: {summary_type}")
        
        if summary_type == "short":
            max_sentences = kwargs.get("max_sentences", 3)
            result = await self.news_summarization.generate_short_summary(text, max_sentences)
        elif summary_type == "topic":
            topic = kwargs.get("topic", "")
            result = await self.news_summarization.generate_topic_summary(text, topic)
        elif summary_type == "multi_view":
            perspectives = kwargs.get("perspectives", [])
            result = await self.news_summarization.generate_multi_view_summary(text, perspectives)
        else:
            result = await self.news_summarization.generate_summary(text)
            
        logger.info(f"新闻摘要生成完成，摘要类型: {summary_type}")
        return result
    
    def aggregate_entities(self, entities: List[Dict[str, Any]], aggregation_type: str = "standard", **kwargs) -> Dict[str, Any]:
        """
        聚合相似实体
        
        Args:
            entities: 实体列表
            aggregation_type: 聚合类型，可选值：standard, by_type, duplicate, merge_attributes
            **kwargs: 其他参数，根据聚合类型不同而不同
            
        Returns:
            包含聚合结果的字典
        """
        logger.info(f"开始聚合实体，聚合类型: {aggregation_type}")
        
        if aggregation_type == "by_type":
            entity_type = kwargs.get("entity_type", "")
            result = self.entity_aggregation.aggregate_entities_by_type(entities, entity_type)
        elif aggregation_type == "duplicate":
            similarity_threshold = kwargs.get("similarity_threshold", 0.8)
            result = self.entity_aggregation.find_duplicate_entities(entities, similarity_threshold)
        elif aggregation_type == "merge_attributes":
            result = self.entity_aggregation.merge_entity_attributes(entities)
        else:
            result = self.entity_aggregation.aggregate_entities(entities)
            
        logger.info(f"实体聚合完成，聚合类型: {aggregation_type}")
        return result
    
    def aggregate_relations(self, relations: List[Dict[str, Any]], aggregation_type: str = "standard", **kwargs) -> Dict[str, Any]:
        """
        聚合相似关系
        
        Args:
            relations: 关系列表
            aggregation_type: 聚合类型，可选值：standard, by_type, duplicate, merge_attributes, consolidate
            **kwargs: 其他参数，根据聚合类型不同而不同
            
        Returns:
            包含聚合结果的字典
        """
        logger.info(f"开始聚合关系，聚合类型: {aggregation_type}")
        
        if aggregation_type == "by_type":
            relation_type = kwargs.get("relation_type", "")
            result = self.relation_aggregation.aggregate_relations_by_type(relations, relation_type)
        elif aggregation_type == "duplicate":
            similarity_threshold = kwargs.get("similarity_threshold", 0.8)
            result = self.relation_aggregation.find_duplicate_relations(relations, similarity_threshold)
        elif aggregation_type == "merge_attributes":
            result = self.relation_aggregation.merge_relation_attributes(relations)
        elif aggregation_type == "consolidate":
            entities = kwargs.get("entities", [])
            result = self.relation_aggregation.consolidate_relations(relations, entities)
        else:
            result = self.relation_aggregation.aggregate_relations(relations)
            
        logger.info(f"关系聚合完成，聚合类型: {aggregation_type}")
        return result
    
    def process_news_text(self, text: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理新闻文本，执行完整的流程：实体抽取、关系抽取、新闻摘要、实体聚合、关系聚合
        
        Args:
            text: 新闻文本
            options: 处理选项，包含各种参数
            
        Returns:
            包含所有处理结果的字典
        """
        options = options or {}
        logger.info(f"开始处理新闻文本，文本长度: {len(text)}")
        
        # 1. 实体抽取
        entity_types = options.get("entity_types")
        entities_result = self.extract_entities(text, entity_types)
        entities = entities_result.get("entities", [])
        
        # 2. 关系抽取
        relations_result = self.extract_relations(text, entities)
        relations = relations_result.get("relations", [])
        
        # 3. 新闻摘要
        summary_type = options.get("summary_type", "standard")
        summary_kwargs = {k: v for k, v in options.items() 
                         if k in ["max_sentences", "topic", "perspectives"]}
        summary_result = self.generate_news_summary(text, summary_type, **summary_kwargs)
        
        # 4. 实体聚合
        entity_aggregation_type = options.get("entity_aggregation_type", "standard")
        entity_agg_kwargs = {k: v for k, v in options.items() 
                            if k in ["entity_type", "similarity_threshold"]}
        entity_aggregation_result = self.aggregate_entities(entities, entity_aggregation_type, **entity_agg_kwargs)
        
        # 5. 关系聚合
        relation_aggregation_type = options.get("relation_aggregation_type", "standard")
        relation_agg_kwargs = {k: v for k, v in options.items() 
                             if k in ["relation_type", "similarity_threshold", "entities"]}
        
        # 如果关系聚合类型是consolidate，需要传入聚合后的实体
        if relation_aggregation_type == "consolidate":
            relation_agg_kwargs["entities"] = entity_aggregation_result.get("aggregated_entities", [])
            
        relation_aggregation_result = self.aggregate_relations(relations, relation_aggregation_type, **relation_agg_kwargs)
        
        # 整合所有结果
        result = {
            "entities": entities_result,
            "relations": relations_result,
            "summary": summary_result,
            "entity_aggregation": entity_aggregation_result,
            "relation_aggregation": relation_aggregation_result,
            "processing_options": options
        }
        
        logger.info("新闻文本处理完成")
        return result
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态信息
        
        Returns:
            包含服务状态的字典
        """
        return {
            "service_name": "LLMService",
            "config": {
                "model": self.config.model,
                "temperature": self.config.temperature,
                "base_url": self.config.base_url
            },
            "services": {
                "entity_extraction": "EntityExtractionService",
                "relation_extraction": "RelationExtractionService",
                "news_summarization": "NewsSummarizationService",
                "entity_aggregation": "EntityAggregationService",
                "relation_aggregation": "RelationAggregationService"
            },
            "status": "running"
        }