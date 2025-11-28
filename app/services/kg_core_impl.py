"""
KG核心实现服务
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.base_service import BaseService
from app.core.content_summarizer import ContentSummarizer
from app.core.content_processor import ContentProcessor
from app.core.entity_analyzer import EntityAnalyzer
from app.core.extract_models import Entity, Relation, KnowledgeGraph
from app.store import HybridStoreCore
from app.config.config_manager import ConfigManager
from app.services.kg_core_abstract import KGCoreAbstractService
from app.database.manager import DatabaseManager, init_database
from app.database.core import DatabaseConfig
from app.vector.vector_service import VectorSearchService
from app.embedding import EmbeddingService
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class KGCoreImplService(BaseService,KGCoreAbstractService):
    """KG核心实现服务"""

    def __init__(self, content_processor=None, entity_analyzer=None, content_summarizer=None, llm_service=None, embedding_dimension: Optional[int] = None, auto_init_store: bool = True):
        super().__init__(llm_service=llm_service)
        self.config = ConfigManager()
        self.content_processor = content_processor or ContentProcessor(llm_service=llm_service)
        self.entity_analyzer = entity_analyzer or EntityAnalyzer(llm_service=llm_service)
        self.content_summarizer = content_summarizer or ContentSummarizer(llm_service=llm_service)
        self.store: Optional[HybridStoreCore] = None
        
        # 初始化embedding维度：优先使用传入参数，其次从配置获取
        self._embedding_dimension = embedding_dimension or self._get_embedding_dimension_from_config()
        
        # 自动初始化store
        if auto_init_store:
            self._init_store()
                
        logger.info("KGCoreImplService 初始化完成")
    
    def _get_embedding_dimension_from_config(self) -> Optional[int]:
        """从配置获取embedding维度"""
        embedding_config = self.config.get_embedding_config()
        vector_config = self.config.get_vector_search_config()
        
        # 优先使用embedding配置的维度，其次使用向量搜索配置的维度
        dimension = getattr(embedding_config, 'dimension', None) or getattr(vector_config, 'dimension', None)
        
        if dimension:
            logger.info(f"从配置获取embedding维度: {dimension}")
        else:
            logger.info("未找到embedding维度配置")
        
        return dimension
    
    async def _get_embedding_dimension_from_service(self) -> int:
        """从embedding服务获取维度"""
        try:
            if hasattr(self.store, 'embedding_service') and self.store.embedding_service:
                # 通过实际生成测试向量来获取维度
                test_embedding = await self.store.embedding_service.embed_text("测试")
                dimension = len(test_embedding)
                logger.info(f"成功从embedding服务获取维度: {dimension}")
                return dimension
            else:
                logger.warning("未找到embedding服务，使用默认维度")
                return 1536  # 默认维度
        except Exception as e:
            logger.warning(f"无法从embedding服务获取维度: {e}, 使用默认值")
            return 1536  # 默认维度
    
    async def _init_store(self):
        """自动初始化store实例"""
        try:
            logger.info("开始自动初始化store...")
            
            # 1. 初始化数据库管理器
            db_config_obj = self.config.get_database_config()
            db_config = DatabaseConfig(
                database_url=db_config_obj.url,
                echo=db_config_obj.echo,
                pool_pre_ping=db_config_obj.pool_pre_ping,
                pool_recycle=db_config_obj.pool_recycle
            )
            db_manager = init_database(db_config)
            logger.info("数据库管理器初始化完成")
            
            # 2. 初始化向量搜索服务
            vector_service = VectorSearchService()
            vector_store = vector_service.get_vector_search()
            logger.info("向量搜索服务初始化完成")
            
            # 3. 初始化embedding服务
            embedding_service = EmbeddingService()
            logger.info("embedding服务初始化完成")
            
            # 4. 创建store实例
            self.store = HybridStoreCore(
                db_manager=db_manager,
                vector_store=vector_store,
                embedding_service=embedding_service
            )
            
            # 5. 初始化store
            await self.store.initialize()
            logger.info("store自动初始化完成")
            
            # 6. 获取embedding维度（如果之前未设置）
            if self._embedding_dimension is None:
                self._embedding_dimension = 1536  # 默认维度
                logger.info(f"使用默认embedding维度: {self._embedding_dimension}")
            
        except Exception as e:
            logger.error(f"store自动初始化失败: {e}")
            raise RuntimeError(f"store自动初始化失败: {e}")

    @property
    def embedding_dimension(self) -> Optional[int]:
        """
        获取embedding维度
        
        Returns:
            Optional[int]: embedding维度，如果未指定则返回None
        """
        return self._embedding_dimension

    async def initialize(self, store: Optional[HybridStoreCore] = None) -> None:
        """
        初始化服务，设置存储实例
        
        Args:
            store: 可选的store实例，如果不提供则使用自动初始化的store
        """
        if store is not None:
            self.store = store
            logger.info("使用提供的store实例")
        elif self.store is None:
            logger.info("store未初始化，进行自动初始化...")
            await self._init_store()
        
        if self.store is None:
            raise RuntimeError("store未初始化，无法继续")
        
        logger.info("KGCoreImplService 存储初始化完成")
        
        # 记录当前使用的embedding维度信息
        if self._embedding_dimension:
            logger.info(f"使用embedding维度: {self._embedding_dimension}")
        else:
            # 如果仍未获取到维度，尝试从store的embedding服务获取
            self._embedding_dimension = await self._get_embedding_dimension_from_service()
            logger.info(f"从embedding服务获取维度: {self._embedding_dimension}")

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
        
        # 参数验证（在try块外，确保ValueError直接抛出）
        if not content or not content.strip():
            raise ValueError("内容不能为空")
        
        try:
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
            if classification_result and classification_result.category:
                category_name = classification_result.category
                logger.info(f"使用分类: {category_name}")
            else:
                raise ValueError("无法获取分类结果")
            category_info = category_config.get(category_name, {})
            
            entity_types = category_info.get('entity_types', kg_config.entity_types)
            relation_types = category_info.get('relation_types', kg_config.relation_types)
            
            extraction_result = await self.content_processor.extract_entities_and_relations(
                content, 
                entity_types=entity_types,
                relation_types=relation_types
            )
            logger.info(f"提取到 {len(extraction_result.knowledge_graph.entities)} 个实体, {len(extraction_result.knowledge_graph.relations)} 个关系")
            
            # 处理实体：向量查找、消歧、合并存储
            processed_entities = await self._process_entities_with_vector_search(extraction_result.knowledge_graph.entities)
            
            # 处理关系
            await self._process_relations(extraction_result.knowledge_graph.relations, processed_entities)
            
            # 根据content_summarizer 对内容进行摘要,并存储摘要,并与实体关联
            summary = await self._process_content_summary(content, processed_entities)
            
            # 构建知识图谱
            metadata = {
                "content_id": content_id,
                "content_length": len(content),
                "extraction_timestamp": datetime.now().isoformat(),
                "summary": summary
            }
            
            knowledge_graph = KnowledgeGraph(
                entities=list(processed_entities.values()),
                relations=extraction_result.knowledge_graph.relations,
                category=classification_result.category,
                metadata=metadata
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
        total_entities = len(entities)
        logger.info(f"开始处理实体列表，共 {total_entities} 个实体")
        
        for i, entity in enumerate(entities):
            try:
                logger.info(f"处理实体 {i+1}/{total_entities}: '{entity.name}' (类型: {entity.type})")
                
                # 根据store中存储的方法，根据向量查找，找到对应的相似向量
                logger.debug(f"正在搜索相似实体: '{entity.name}'")
                similar_entities = await self.store.search_entities(
                    query=entity.name,
                    entity_type=entity.type,
                    top_k=5,
                    include_vector_search=True,
                    include_full_text_search=False
                )
                
                logger.info(f"找到 {len(similar_entities)} 个相似实体")
                
                if not similar_entities:
                    logger.info(f"未找到相似实体，将创建新的实体: '{entity.name}'")
                    # 如果无重复，直接存储实体以及对应的关系
                    logger.info(f"存储新实体: '{entity.name}'")
                    stored_entity = await self.store.create_entity(entity)
                    logger.info(
                        f"成功存储实体: {stored_entity.name} (ID: {stored_entity.id}, 类型: {stored_entity.type})")
                    processed_entities[entity.name] = stored_entity
                    continue

                is_all_match = False
                for result in similar_entities:
                    if result.entity and result.entity.name == entity.name:
                        processed_entities[entity.name] = result.entity
                        logger.info(f"已找到匹配实体: '{result.entity.name}'")
                        is_all_match = True
                if is_all_match:
                    continue

                candidate_entities = [result.entity for result in similar_entities if result.entity and result.entity.name != entity.name]
                logger.debug(f"候选实体: {[e.name for e in candidate_entities]}")


                logger.info(f"解析实体 '{entity.name}' 的歧义...")
                ambiguity_result = await self.entity_analyzer.resolve_entity_ambiguity(
                        entity, candidate_entities
                )

                logger.info(f"歧义解析结果: 选中实体={ambiguity_result.selected_entity.name if ambiguity_result.selected_entity else '无'}, 置信度={ambiguity_result.confidence}")

                if ambiguity_result.selected_entity:
                        # 如果有选中的实体，使用选中的实体
                    selected_entity = ambiguity_result.selected_entity
                    logger.info(f"实体 '{entity.name}' 与选中实体 '{selected_entity.name}' 匹配 (置信度: {ambiguity_result.confidence})")
                    processed_entities[entity.name] = selected_entity
                else:
                    # 如果没有选中的实体，创建新实体
                    logger.info(f"未选中任何候选实体，将创建新实体: '{entity.name}'")
                    stored_entity = await self.store.create_entity(entity)
                    logger.info(f"成功存储新实体: {stored_entity.name} (ID: {stored_entity.id}, 类型: {stored_entity.type})")
                    processed_entities[entity.name] = stored_entity

            except Exception as e:
                logger.error(f"处理实体 '{entity.name}' 失败: {e}")
                continue
        
        logger.info(f"实体处理完成，共处理 {len(processed_entities)} 个有效实体")
        return processed_entities

    async def _process_relations(self, relations: List[Relation], entity_map: Dict[str, Entity]) -> None:
        """
        处理关系列表：基于处理后的实体存储关系
        
        Args:
            relations: 待处理的关系列表
            entity_map: 实体名称到实体对象的映射
        """
        total_relations = len(relations)
        logger.info(f"开始处理关系列表，共 {total_relations} 个关系")
        
        for i, relation in enumerate(relations):
            try:
                logger.info(f"处理关系 {i+1}/{total_relations}: {relation.subject} -> {relation.predicate} -> {relation.object}")
                
                # 获取主体和客体实体
                subject_entity = entity_map.get(relation.subject)
                object_entity = entity_map.get(relation.object)
                
                if not subject_entity:
                    logger.warning(f"关系 '{relation.subject} -> {relation.object}' 缺少主体实体 '{relation.subject}'，跳过")
                    continue
                
                if not object_entity:
                    logger.warning(f"关系 '{relation.subject} -> {relation.object}' 缺少客体实体 '{relation.object}'，跳过")
                    continue
                
                logger.info(f"找到实体: 主体='{subject_entity.name}' (ID: {subject_entity.id}), 客体='{object_entity.name}' (ID: {object_entity.id})")
                
                # 更新关系中的实体ID
                relation.subject_id = subject_entity.id
                relation.object_id = object_entity.id
                
                logger.info(f"存储关系: {relation.subject} -> {relation.predicate} -> {relation.object}")
                # 存储关系
                stored_relation = await self.store.create_relation(relation)
                logger.info(f"成功存储关系: {relation.subject} -> {relation.object} (ID: {stored_relation.id}, 谓词: {relation.predicate})")
                
            except Exception as e:
                logger.error(f"处理关系 '{relation.subject} -> {relation.object}' 失败: {e}")
                continue
        
        logger.info(f"关系处理完成，共处理 {total_relations} 个关系")
        
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
            logger.info(f"开始生成内容摘要，内容长度: {len(content)} 字符")
            
            # 生成内容摘要
            summary_result = await self.content_summarizer.generate_summary(content)
            logger.info(f"生成摘要完成，长度: {len(summary_result.summary)} 字符")
            entity_names = list(entities.keys())
            logger.info(f"摘要与以下 {len(entity_names)} 个实体关联: {entity_names[:10]}")  # 只显示前10个
            if len(entity_names) > 10:
                logger.info(f"... 还有 {len(entity_names) - 10} 个实体")
            return summary_result.summary
            
        except Exception as e:
            logger.error(f"处理内容摘要失败: {e}")
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

    @staticmethod
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
        解析LLM响应（已废弃 - 未在代码中使用）
        
        Args:
            response: 大模型响应文本
            
        Returns:
            解析后的响应数据
        """
        return response


