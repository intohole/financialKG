"""
KG核心实现服务
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.base_service import BaseService
from app.core.content_summarizer import ContentSummarizer
from app.core.content_processor import ContentProcessor
from app.core.entity_analyzer import EntityAnalyzer
from app.core.models import Entity, Relation, ContentClassification, ContentCategory, KnowledgeGraph
from app.store import HybridStoreCore
from app.config.config_manager import ConfigManager
from app.services.kg_core_abstract import KGCoreAbstractService

logger = logging.getLogger(__name__)


class KGCoreImplService(BaseService, KGCoreAbstractService):
    """KG核心实现服务"""

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.content_processor = ContentProcessor()
        self.entity_analyzer = EntityAnalyzer()
        self.content_summarizer = ContentSummarizer()
        self.store: Optional[HybridStoreCore] = None
        logger.info("KGCoreImplService 初始化完成")

    async def initialize(self, store: HybridStoreCore) -> None:
        """
        初始化服务，设置存储实例
        
        Args:
            store: 混合存储实例
        """
        self.store = store
        logger.info("KGCoreImplService 存储初始化完成")

    async def process_content(self, content: str, content_id: Optional[str] = None) -> KnowledgeGraph:
        """
        处理内容并构建知识图谱：严格按照todo要求实现核心流程
        
        Args:
            content: 要处理的文本内容
            content_id: 内容ID（可选）
            
        Returns:
            KnowledgeGraph: 构建的知识图谱
            
        Raises:
            ValueError: 当内容为空或无效时
            RuntimeError: 当处理过程中出现错误时
        """
        if not self.store:
            raise RuntimeError("存储未初始化，请先调用initialize方法")
        
        try:
            if not content or not content.strip():
                raise ValueError("内容不能为空")
            
            logger.info(f"开始处理内容，长度: {len(content)}")
            
            # 获取类别变量，通过content_processor.classify_content 获取分类
            kg_config = self.config.get_knowledge_graph_config()
            category_config = self.config.get_config().get('knowledge_graph', {}).get('categories', {})
            classification_result = await self.content_processor.classify_content(
                content, 
                category_config=category_config
            )
            logger.info(f"内容分类结果: {classification_result.category}, 置信度: {classification_result.confidence}")
            
            # 根据获取到的分类，使用self.content_processor.extract_entities_and_relations 获取实体和实体关系
            category_name = classification_result.category.value if hasattr(classification_result.category, 'value') else str(classification_result.category)
            category_info = category_config.get(category_name, {})
            
            entity_types = category_info.get('entity_types', kg_config.entity_types)
            relation_types = category_info.get('relation_types', kg_config.relation_types)
            
            extraction_result = await self.content_processor.extract_entities_and_relations(
                content, 
                entity_types=entity_types,
                relation_types=relation_types
            )
            logger.info(f"提取到 {len(extraction_result.entities)} 个实体, {len(extraction_result.relations)} 个关系")
            
            # 处理实体：向量查找、消歧、合并存储
            processed_entities = await self._process_entities_with_vector_search(extraction_result.entities)
            
            # 处理关系
            await self._process_relations(extraction_result.relations, processed_entities)
            
            # 根据content_summarizer 对内容进行摘要,并存储摘要,并与实体关联
            summary = await self._process_content_summary(content, processed_entities)
            
            # 构建知识图谱
            knowledge_graph = KnowledgeGraph(
                entities=list(processed_entities.values()),
                relations=extraction_result.relations,
                category=classification_result.category,
                summary=summary,
                metadata={
                    "content_id": content_id,
                    "content_length": len(content),
                    "extraction_timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info("内容处理完成")
            return knowledge_graph
            
        except Exception as e:
            logger.error(f"处理内容失败: {e}")
            raise RuntimeError(f"处理内容失败: {str(e)}")

    async def _process_entities_with_vector_search(self, entities: List[Entity]) -> Dict[str, Entity]:
        """
        处理实体列表：严格按照todo要求实现向量查找、消歧、合并存储
        
        Args:
            entities: 待处理的实体列表
            
        Returns:
            处理后的实体映射（实体名称 -> 实体对象）
        """
        processed_entities = {}
        
        for entity in entities:
            try:
                # 根据store中存储的方法，根据向量查找，找到对应的相似向量
                similar_entities = await self.store.search_entities(
                    query=entity.name,
                    entity_type=entity.type,
                    top_k=5,
                    include_vector_search=True,
                    include_full_text_search=False
                )
                
                if similar_entities:
                    # 获取相似向量，通过 entity_analyzer.resolve_entity_ambiguity 解析实体歧义
                    candidate_entities = [result.entity for result in similar_entities if result.entity]
                    
                    ambiguity_result = await self.entity_analyzer.resolve_entity_ambiguity(
                        entity, candidate_entities
                    )
                    
                    if ambiguity_result.is_duplicate and ambiguity_result.best_match:
                        # 如果有重复合并实体
                        existing_entity = ambiguity_result.best_match
                        logger.info(f"实体 '{entity.name}' 与现有实体 '{existing_entity.name}' 重复，合并使用现有实体")
                        processed_entities[entity.name] = existing_entity
                        continue
                
                # 如果无重复，直接存储实体以及对应的关系
                stored_entity = await self.store.create_entity(entity)
                logger.info(f"存储新实体: {stored_entity.name} (ID: {stored_entity.id})")
                processed_entities[entity.name] = stored_entity
                
            except Exception as e:
                logger.error(f"处理实体 '{entity.name}' 失败: {e}")
                # 继续处理其他实体，不中断整个流程
                continue
        
        return processed_entities

    async def _process_relations(self, relations: List[Relation], entity_map: Dict[str, Entity]) -> None:
        """
        处理关系列表：基于处理后的实体存储关系
        
        Args:
            relations: 待处理的关系列表
            entity_map: 实体名称到实体对象的映射
        """
        for relation in relations:
            try:
                # 获取主体和客体实体
                subject_entity = entity_map.get(relation.subject)
                object_entity = entity_map.get(relation.object)
                
                if not subject_entity or not object_entity:
                    logger.warning(f"关系 '{relation.subject} -> {relation.object}' 缺少实体，跳过")
                    continue
                
                # 更新关系中的实体ID
                relation.subject_id = subject_entity.id
                relation.object_id = object_entity.id
                
                # 存储关系
                stored_relation = await self.store.create_relation(relation)
                logger.info(f"存储关系: {relation.subject} -> {relation.object} (ID: {stored_relation.id})")
                
            except Exception as e:
                logger.error(f"处理关系 '{relation.subject} -> {relation.object}' 失败: {e}")
                continue

    async def _process_content_summary(self, content: str, entities: Dict[str, Entity]) -> str:
        """
        处理内容摘要：生成摘要并与实体关联
        
        Args:
            content: 原始内容
            entities: 处理后的实体映射
            
        Returns:
            生成的摘要内容
        """
        try:
            # 生成内容摘要
            summary_result = await self.content_summarizer.summarize(content)
            logger.info(f"生成摘要，长度: {len(summary_result.summary)}")
            
            # 关联摘要与实体（示例：记录日志）
            entity_names = list(entities.keys())
            logger.info(f"摘要与以下实体关联: {entity_names}")
            
            return summary_result.summary
            
        except Exception as e:
            logger.error(f"处理内容摘要失败: {e}")
            # 摘要失败不影响主流程，返回空字符串
            return ""

    async def query_knowledge(self, query: str) -> str:
        """
        查询知识图谱
        
        Args:
            query: 查询语句
            
        Returns:
            查询结果
        """
        if not self.store:
            raise RuntimeError("存储未初始化，请先调用initialize方法")
        
        try:
            logger.info(f"开始查询知识图谱: {query}")
            
            # 1. 向量搜索查找相关实体
            search_results = await self.store.search_entities(
                query=query,
                top_k=10,
                include_vector_search=True,
                include_full_text_search=True
            )
            
            if not search_results:
                return "未找到相关知识"
            
            # 2. 构建查询上下文
            context = self._build_query_context(search_results)
            
            # 3. 使用大模型生成回答
            response = await self.generate_with_prompt(
                "query_kg",
                query=query,
                context=context
            )
            
            logger.info("知识图谱查询完成")
            return response
            
        except Exception as e:
            logger.error(f"查询知识图谱失败: {e}")
            raise RuntimeError(f"查询知识图谱失败: {str(e)}")

    def _build_query_context(self, search_results: List) -> str:
        """
        构建查询上下文
        
        Args:
            search_results: 搜索结果列表
            
        Returns:
            格式化的上下文字符串
        """
        context_parts = []
        
        for result in search_results:
            if result.entity:
                entity_info = f"实体: {result.entity.name} ({result.entity.type})"
                if result.entity.description:
                    entity_info += f" - {result.entity.description}"
                context_parts.append(entity_info)
        
        return "\n".join(context_parts)

    async def parse_llm_response(self, response: str) -> Any:
        """
        解析LLM响应
        
        Args:
            response: 大模型响应文本
            
        Returns:
            解析后的响应数据
        """
        # 直接返回响应文本，或根据需要进行解析
        return response


