"""
知识图谱构建服务 - 核心业务逻辑编排

负责协调内容处理、实体分析、存储管理等模块，实现知识图谱的自动化构建流程。
提供从原始内容到结构化知识图谱的完整处理链路。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.core.content_processor import ContentProcessor
from app.core.entity_analyzer import EntityAnalyzer
from app.core.content_summarizer import ContentSummarizer
from app.store.hybrid_store_core_implement import HybridStoreCore
from app.core.models import ContentClassification, Entity, Relation, KnowledgeGraph, ContentSummary
from app.services.service_models import NewsContent


logger = logging.getLogger(__name__)


@dataclass
class KnowledgeGraphBuildResult:
    """知识图谱构建结果"""
    success: bool
    news_id: str
    entities_extracted: int
    relations_extracted: int
    entities_stored: int
    relations_stored: int
    processing_time: float
    errors: List[str]
    warnings: List[str]


@dataclass
class KnowledgeGraphQueryResult:
    """知识图谱查询结果"""
    entities: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    total_count: int
    query_time: float


class KnowledgeGraphBuilder:
    """知识图谱构建服务"""
    
    def __init__(
        self,
        content_processor: ContentProcessor,
        entity_analyzer: EntityAnalyzer,
        content_summarizer: ContentSummarizer,
        store: HybridStoreCore
    ):
        self.content_processor = content_processor
        self.entity_analyzer = entity_analyzer
        self.content_summarizer = content_summarizer
        self.store = store
        
        logger.info("知识图谱构建服务初始化完成")
    
    async def build_from_news(
        self, 
        news_content: NewsContent,
        enable_entity_linking: bool = True,
        enable_relation_validation: bool = True
    ) -> KnowledgeGraphBuildResult:
        """
        从新闻内容构建知识图谱
        
        Args:
            news_content: 新闻内容对象
            enable_entity_linking: 是否启用实体链接
            enable_relation_validation: 是否启用关系验证
            
        Returns:
            构建结果
        """
        start_time = asyncio.get_event_loop().time()
        errors = []
        warnings = []
        
        try:
            logger.info(f"开始构建知识图谱，新闻ID: {news_content.id}")
            
            # 1. 内容分类和预处理
            classification = await self._classify_content(news_content)
            if not classification:
                errors.append("内容分类失败")
                return self._build_error_result(news_content.id, errors, start_time)
            
            # 2. 实体和关系提取
            entities, relations = await self._extract_entities_and_relations(
                news_content, classification
            )
            
            if not entities:
                warnings.append("未提取到任何实体")
            
            # 3. 实体消歧和标准化
            if enable_entity_linking and entities:
                entities = await self._disambiguate_entities(entities)
            
            # 4. 关系验证和优化
            if enable_relation_validation and relations:
                relations = await self._validate_relations(entities, relations)
            
            # 5. 存储到知识图谱
            entities_stored = await self._store_entities(news_content.id, entities)
            relations_stored = await self._store_relations(news_content.id, relations)
            
            # 6. 更新新闻事件信息
            await self._update_news_event(news_content, classification)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = KnowledgeGraphBuildResult(
                success=True,
                news_id=news_content.id,
                entities_extracted=len(entities),
                relations_extracted=len(relations),
                entities_stored=entities_stored,
                relations_stored=relations_stored,
                processing_time=processing_time,
                errors=errors,
                warnings=warnings
            )
            
            logger.info(f"知识图谱构建完成，耗时: {processing_time:.2f}s，"
                       f"实体: {entities_stored}, 关系: {relations_stored}")
            
            return result
            
        except Exception as e:
            logger.error(f"知识图谱构建失败: {str(e)}", exc_info=True)
            errors.append(f"构建过程异常: {str(e)}")
            return self._build_error_result(news_content.id, errors, start_time)
    
    async def _classify_content(self, news_content: NewsContent) -> Optional[ContentClassification]:
        """内容分类"""
        try:
            result = await self.content_processor.classify_content(
                content=news_content.content,
                title=news_content.title
            )
            
            if result and hasattr(result, 'classification'):
                logger.debug(f"内容分类结果: {result.classification}")
                return result
            
            logger.warning("内容分类未返回有效结果")
            return None
            
        except Exception as e:
            logger.error(f"内容分类失败: {str(e)}")
            return None
    
    async def _extract_entities_and_relations(
        self, 
        news_content: NewsContent, 
        classification: ContentClassification
    ) -> Tuple[List[Dict], List[Dict]]:
        """提取实体和关系"""
        try:
            # 提取实体和关系
            extraction_result = await self.content_processor.extract_entities_and_relations(
                content=news_content.content,
                content_type=classification.classification if classification else "news"
            )
            
            entities = []
            relations = []
            
            if extraction_result and hasattr(extraction_result, 'entities'):
                entities = extraction_result.entities
                logger.debug(f"提取到 {len(entities)} 个实体")
            
            if extraction_result and hasattr(extraction_result, 'relations'):
                relations = extraction_result.relations
                logger.debug(f"提取到 {len(relations)} 个关系")
            
            return entities, relations
            
        except Exception as e:
            logger.error(f"实体关系提取失败: {str(e)}")
            return [], []
    
    async def _disambiguate_entities(self, entities: List[Dict]) -> List[Dict]:
        """实体消歧"""
        try:
            if not entities:
                return entities
            
            # 对相似实体进行消歧
            disambiguated_entities = []
            processed_names = set()
            
            for entity in entities:
                entity_name = entity.get('name', '')
                if entity_name in processed_names:
                    continue
                
                # 查找相似实体
                similar_entities = await self.entity_analyzer.find_similar_entities(
                    entity_name=entity_name,
                    entity_type=entity.get('type', 'unknown')
                )
                
                if similar_entities and len(similar_entities) > 0:
                    # 选择最相似的实体作为标准实体
                    best_match = similar_entities[0]
                    if best_match.similarity_score > 0.8:  # 相似度阈值
                        # 使用标准实体信息
                        entity['standard_name'] = best_match.entity_name
                        entity['disambiguation_score'] = best_match.similarity_score
                    else:
                        entity['standard_name'] = entity_name
                        entity['disambiguation_score'] = 1.0
                else:
                    entity['standard_name'] = entity_name
                    entity['disambiguation_score'] = 1.0
                
                processed_names.add(entity_name)
                disambiguated_entities.append(entity)
            
            logger.debug(f"实体消歧完成，处理 {len(disambiguated_entities)} 个实体")
            return disambiguated_entities
            
        except Exception as e:
            logger.error(f"实体消歧失败: {str(e)}")
            return entities
    
    async def _validate_relations(
        self, 
        entities: List[Dict], 
        relations: List[Dict]
    ) -> List[Dict]:
        """关系验证"""
        try:
            if not relations:
                return relations
            
            validated_relations = []
            entity_names = {entity.get('standard_name', entity.get('name', '')) 
                          for entity in entities}
            
            for relation in relations:
                source_entity = relation.get('source_entity', '')
                target_entity = relation.get('target_entity', '')
                
                # 验证关系两端的实体是否存在
                if source_entity in entity_names and target_entity in entity_names:
                    # 验证关系类型是否合理
                    relation_type = relation.get('relation_type', '')
                    if self._is_valid_relation_type(relation_type):
                        validated_relations.append(relation)
                    else:
                        logger.warning(f"无效的关系类型: {relation_type}")
                else:
                    logger.warning(f"关系实体不存在: {source_entity} -> {target_entity}")
            
            logger.debug(f"关系验证完成，有效关系: {len(validated_relations)}")
            return validated_relations
            
        except Exception as e:
            logger.error(f"关系验证失败: {str(e)}")
            return relations
    
    def _is_valid_relation_type(self, relation_type: str) -> bool:
        """验证关系类型是否有效"""
        valid_types = {
            '所属', '位于', '涉及', '影响', '导致', '参与', '拥有', '生产',
            '销售', '合作', '竞争', '投资', '收购', '合并', '子公司',
            '母公司', '股东', '高管', '员工', '客户', '供应商'
        }
        return relation_type in valid_types
    
    async def _store_entities(self, news_id: str, entities: List[Dict]) -> int:
        """存储实体到知识图谱"""
        try:
            stored_count = 0
            
            for entity in entities:
                entity_data = {
                    'name': entity.get('standard_name', entity.get('name', '')),
                    'type': entity.get('type', 'unknown'),
                    'properties': entity.get('properties', {}),
                    'source_news': news_id,
                    'confidence': entity.get('confidence', 0.8),
                    'disambiguation_score': entity.get('disambiguation_score', 1.0)
                }
                
                # 存储实体
                success = await self.store.add_entity(**entity_data)
                if success:
                    stored_count += 1
            
            logger.debug(f"存储实体完成，成功: {stored_count}/{len(entities)}")
            return stored_count
            
        except Exception as e:
            logger.error(f"实体存储失败: {str(e)}")
            return 0
    
    async def _store_relations(self, news_id: str, relations: List[Dict]) -> int:
        """存储关系到知识图谱"""
        try:
            stored_count = 0
            
            for relation in relations:
                relation_data = {
                    'source_entity': relation.get('source_entity', ''),
                    'target_entity': relation.get('target_entity', ''),
                    'relation_type': relation.get('relation_type', ''),
                    'properties': relation.get('properties', {}),
                    'source_news': news_id,
                    'confidence': relation.get('confidence', 0.8)
                }
                
                # 存储关系
                success = await self.store.add_relation(**relation_data)
                if success:
                    stored_count += 1
            
            logger.debug(f"存储关系完成，成功: {stored_count}/{len(relations)}")
            return stored_count
            
        except Exception as e:
            logger.error(f"关系存储失败: {str(e)}")
            return 0
    
    async def _update_news_event(self, news_content: NewsContent, classification: ContentClassification):
        """更新新闻事件信息"""
        try:
            event_data = {
                'news_id': news_content.id,
                'title': news_content.title,
                'content': news_content.content,
                'publish_time': news_content.publish_time,
                'source': news_content.source,
                'category': classification.classification if classification else 'unknown',
                'importance_score': getattr(classification, 'confidence', 0.8)
            }
            
            await self.store.add_news_event(**event_data)
            logger.debug(f"新闻事件信息已更新: {news_content.id}")
            
        except Exception as e:
            logger.error(f"新闻事件更新失败: {str(e)}")
    
    def _build_error_result(
        self, 
        news_id: str, 
        errors: List[str], 
        start_time: float
    ) -> KnowledgeGraphBuildResult:
        """构建错误结果"""
        processing_time = asyncio.get_event_loop().time() - start_time
        return KnowledgeGraphBuildResult(
            success=False,
            news_id=news_id,
            entities_extracted=0,
            relations_extracted=0,
            entities_stored=0,
            relations_stored=0,
            processing_time=processing_time,
            errors=errors,
            warnings=[]
        )
    
    async def query_knowledge_graph(
        self,
        entity_name: Optional[str] = None,
        entity_type: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100
    ) -> KnowledgeGraphQueryResult:
        """
        查询知识图谱
        
        Args:
            entity_name: 实体名称
            entity_type: 实体类型
            relation_type: 关系类型
            limit: 返回结果数量限制
            
        Returns:
            查询结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            entities = []
            relations = []
            
            # 查询实体
            if entity_name or entity_type:
                entities = await self.store.search_entities(
                    name=entity_name,
                    entity_type=entity_type,
                    limit=limit
                )
            
            # 查询关系
            if entity_name or relation_type:
                relations = await self.store.search_relations(
                    entity_name=entity_name,
                    relation_type=relation_type,
                    limit=limit
                )
            
            query_time = asyncio.get_event_loop().time() - start_time
            
            result = KnowledgeGraphQueryResult(
                entities=entities,
                relations=relations,
                total_count=len(entities) + len(relations),
                query_time=query_time
            )
            
            logger.info(f"知识图谱查询完成，耗时: {query_time:.2f}s，"
                       f"实体: {len(entities)}, 关系: {len(relations)}")
            
            return result
            
        except Exception as e:
            logger.error(f"知识图谱查询失败: {str(e)}")
            return KnowledgeGraphQueryResult(
                entities=[],
                relations=[],
                total_count=0,
                query_time=asyncio.get_event_loop().time() - start_time
            )