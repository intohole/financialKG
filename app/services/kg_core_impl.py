"""
KG核心实现服务
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.base_service import BaseService
from app.core.content_summarizer import ContentSummarizer
from app.core.content_processor import ContentProcessor
from app.core.entity_analyzer import EntityAnalyzer
from app.core.extract_models import Entity, Relation, KnowledgeGraph, ContentSummary
from app.store.store_base_abstract import NewsEvent
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
        
        # 自动初始化store（延迟到需要时再进行）
        self._auto_init_pending = auto_init_store
                
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
    
    async def _ensure_store_initialized(self):
        """确保store已初始化"""
        if self.store is None and self._auto_init_pending:
            logger.info("需要自动初始化store...")
            await self._init_store()
            self._auto_init_pending = False
            
    def _validate_store_initialized(self) -> bool:
        """验证store是否已初始化
        
        Returns:
            bool: True表示已初始化，False表示未初始化
        """
        if not self.store:
            logger.error("存储未初始化，请先调用initialize方法")
            return False
        return True
        
    def _handle_operation_error(self, operation: str, error: Exception) -> None:
        """统一处理操作错误
        
        Args:
            operation: 操作名称
            error: 异常对象
        """
        logger.error(f"{operation}失败: {error}", exc_info=True)
        if isinstance(error, (ValueError, RuntimeError)):
            raise
        raise RuntimeError(f"{operation}失败: {str(error)}")

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

    def _log_operation_start(self, operation: str, **kwargs) -> None:
        """记录操作开始日志
        
        Args:
            operation: 操作名称
            **kwargs: 额外的日志参数
        """
        log_parts = [f"开始{operation}"]
        for key, value in kwargs.items():
            log_parts.append(f"{key}: {value}")
        logger.info(", ".join(log_parts))
        
    def _log_operation_success(self, operation: str, **kwargs) -> None:
        """记录操作成功日志
        
        Args:
            operation: 操作名称
            **kwargs: 额外的日志参数
        """
        log_parts = [f"{operation}完成"]
        for key, value in kwargs.items():
            log_parts.append(f"{key}: {value}")
        logger.info(", ".join(log_parts))
            
    async def process_content(self, content: str) -> KnowledgeGraph:
        """
        处理内容并构建知识图谱：严格按照todo要求实现核心流程
        
        Args:
            content: 要处理的文本内容
            
        Returns:
            KnowledgeGraph: 构建的知识图谱
            
        Raises:
            ValueError: 当内容为空或无效时
            RuntimeError: 当处理过程中出现错误时
        """
        import time
        total_start_time = time.time()
        
        try:
            logger.info(f"[START] 开始处理内容，长度: {len(content)}")
            
            # 确保store已初始化
            store_init_time = time.time()
            await self._ensure_store_initialized()
            store_init_elapsed = time.time() - store_init_time
            logger.info(f"[STORE] 存储初始化完成，耗时: {store_init_elapsed:.2f}秒")
            
            if not self._validate_store_initialized():
                raise RuntimeError("存储未初始化，请先调用initialize方法")
            
            # 搜索相似新闻事件
            similar_search_time = time.time()
            similar_events = await self.store.search_news_events(content, top_k=5)
            similar_search_elapsed = time.time() - similar_search_time
            logger.info(f"[SIMILAR] 相似新闻搜索完成，耗时: {similar_search_elapsed:.2f}秒, 找到 {len(similar_events) if similar_events else 0} 条相似新闻")
            
            knowledge_graph_config = self.config.get_knowledge_graph_config()

            # 检查相似性阈值
            if similar_events and max([e.score for e in similar_events]) > knowledge_graph_config.filter_news_similarity_threshold:
                logger.info(f"[SKIP] 新闻过于相似，跳过处理")
                return KnowledgeGraph()

            self._log_operation_start("处理内容", 长度=len(content))
            
            # 1. 内容分类
            classify_time = time.time()
            classification_result = await self.content_processor.classify_content(
                content, 
                categories_prompt=knowledge_graph_config.get_categories_prompt()
            )
            classify_elapsed = time.time() - classify_time
            logger.info(f"[CLASSIFY] 内容分类完成，耗时: {classify_elapsed:.2f}秒, 结果: {classification_result.category}, 置信度: {classification_result.confidence}")
            
            # 确定分类
            category_name = self._get_category_name(classification_result)
            category_info = knowledge_graph_config.categories.get(category_name)
            if not category_info:
                raise ValueError(f"未知的分类: {category_name}")

            # 2. 实体和关系提取
            extract_time = time.time()
            extraction_result = await self.content_processor.extract_entities_and_relations(
                content, 
                entity_types=category_info.get_entity_types_prompt(),
                relation_types=category_info.get_relation_types_prompt()
            )
            extract_elapsed = time.time() - extract_time
            entities_count = len(extraction_result.knowledge_graph.entities)
            relations_count = len(extraction_result.knowledge_graph.relations)
            logger.info(f"[EXTRACT] 实体关系提取完成，耗时: {extract_elapsed:.2f}秒, 实体数量: {entities_count}, 关系数量: {relations_count}")
            
            self._log_operation_start("提取结果", 
                                    实体数量=entities_count,
                                    关系数量=relations_count)
            
            # 3. 处理实体
            process_entity_time = time.time()
            processed_entities = await self._process_entities_with_vector_search(extraction_result.knowledge_graph.entities)
            process_entity_elapsed = time.time() - process_entity_time
            logger.info(f"[PROCESS ENTITY] 实体处理完成，耗时: {process_entity_elapsed:.2f}秒, 处理后实体数量: {len(processed_entities)}")
            
            # 4. 处理关系
            process_relation_time = time.time()
            await self._process_relations(extraction_result.knowledge_graph.relations, processed_entities)
            process_relation_elapsed = time.time() - process_relation_time
            logger.info(f"[PROCESS RELATION] 关系处理完成，耗时: {process_relation_elapsed:.2f}秒")
            
            # 5. 生成摘要
            summary_time = time.time()
            summary_result = await self._process_content_summary(content, processed_entities)
            summary_elapsed = time.time() - summary_time
            logger.info(f"[SUMMARY] 摘要生成完成，耗时: {summary_elapsed:.2f}秒, 标题: {summary_result.title if summary_result else '无'}")
            
            # 6. 创建新闻事件
            news_time = time.time()
            await self._create_news_event_from_summary(
                summary_result, 
                category_name,
                len(processed_entities),
                relations_count,
                processed_entities
            )
            news_elapsed = time.time() - news_time
            logger.info(f"[NEWS] 新闻事件创建完成，耗时: {news_elapsed:.2f}秒")
            
            # 7. 构建并返回知识图谱
            build_time = time.time()
            knowledge_graph = await self._build_knowledge_graph(
                content, 
                processed_entities, 
                extraction_result.knowledge_graph.relations,
                category_name,
                summary_result
            )
            build_elapsed = time.time() - build_time
            logger.info(f"[BUILD] 知识图谱构建完成，耗时: {build_elapsed:.2f}秒")
            
            total_elapsed = time.time() - total_start_time
            self._log_operation_success("内容处理", 总耗时=f"{total_elapsed:.2f}秒")
            logger.info(f"[END] 内容处理完成，总耗时: {total_elapsed:.2f}秒, 最终实体数量: {len(knowledge_graph.entities)}, 最终关系数量: {len(knowledge_graph.relations)}")
            
            return knowledge_graph
            
        except Exception as e:
            total_elapsed = time.time() - total_start_time
            logger.error(f"[ERROR] 内容处理失败，总耗时: {total_elapsed:.2f}秒, 错误: {e}", exc_info=True)
            self._handle_operation_error("处理内容", e)
    
    def _get_category_name(self, classification_result) -> str:
        """获取分类名称
        
        Args:
            classification_result: 分类结果对象
            
        Returns:
            str: 分类名称
        """
        category_name = classification_result.category if classification_result else None
        if not category_name:
            category_name = "general"  # 使用默认分类
            logger.warning(f"无法获取分类结果，使用默认分类: {category_name}")
        else:
            logger.info(f"使用分类: {category_name}")
        return category_name
        
    async def _build_knowledge_graph(self, content: str, entities: Dict[str, Entity], 
                                    relations: List[Relation], category: str, 
                                    summary_result) -> KnowledgeGraph:
        """构建知识图谱
        
        Args:
            content: 原始内容
            entities: 处理后的实体映射
            relations: 提取的关系列表
            category: 内容分类
            summary_result: 摘要结果
            
        Returns:
            KnowledgeGraph: 构建的知识图谱
        """
        metadata = {
            "content_length": len(content),
            "extraction_timestamp": datetime.now().isoformat(),
            "summary": summary_result.summary if summary_result else "",
            "entities_count": len(entities),
            "relations_count": len(relations)
        }
        
        return KnowledgeGraph(
            entities=list(entities.values()),
            relations=relations,
            category=category,
            metadata=metadata
        )

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
                entity_name = entity.name
                # 检查是否已处理过该实体
                if entity_name in processed_entities:
                    logger.debug(f"实体 '{entity_name}' 已处理，跳过")
                    continue
                
                # 根据store中存储的方法，根据向量查找，找到对应的相似向量
                similar_entities = await self.store.search_entities(
                    query=entity_name,
                    entity_type=entity.type,
                    top_k=5,
                    include_vector_search=True,
                    include_full_text_search=False
                )
                
                if not similar_entities:
                    # 未找到相似实体，创建新实体
                    stored_entity = await self.store.create_entity(entity)
                    logger.debug(f"成功存储新实体: {stored_entity.name} (ID: {stored_entity.id}, 类型: {stored_entity.type})")
                    processed_entities[entity_name] = stored_entity
                    continue

                knowledge_config = self.config.get_knowledge_graph_config()
                # 检查是否有完全匹配的实体
                matched_entity = None
                for result in similar_entities:
                    if result.entity and (result.entity.name == entity_name or result.score > knowledge_config.similarity_threshold):
                        matched_entity = result.entity
                        break
                
                if matched_entity:
                    logger.debug(f"已找到匹配实体: '{matched_entity.name}'")
                    processed_entities[entity_name] = matched_entity
                    continue

                # 准备候选实体列表
                candidate_entities = [result.entity for result in similar_entities]
                
                # 解析实体歧义
                ambiguity_result = await self.entity_analyzer.resolve_entity_ambiguity(
                        entity, candidate_entities
                )

                if ambiguity_result.selected_entity:
                    selected_entity = ambiguity_result.selected_entity
                    logger.debug(f"实体 '{entity_name}' 与选中实体 '{selected_entity.name}' 匹配 (置信度: {ambiguity_result.confidence})")
                    processed_entities[entity_name] = selected_entity
                else:
                    # 如果没有选中的实体，创建新实体
                    stored_entity = await self.store.create_entity(entity)
                    logger.debug(f"成功存储新实体: {stored_entity.name} (ID: {stored_entity.id}, 类型: {stored_entity.type})")
                    processed_entities[entity_name] = stored_entity

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
        
    async def _process_content_summary(self, content: str, entities: Dict[str, Entity]) -> Optional[ContentSummary]:
        """
        处理内容摘要：生成摘要并与实体关联
        
        Args:
            content: 原始内容
            entities: 处理后的实体映射
            
        Returns:
            生成的摘要对象，失败时返回None
        """
        try:
            logger.info(f"开始生成内容摘要，内容长度: {len(content)} 字符")
            
            # 生成内容摘要
            summary_result = await self.content_summarizer.generate_summary(content)
            logger.info(f"生成摘要完成，标题: {summary_result.title}, 长度: {len(summary_result.summary)} 字符")
            entity_names = list(entities.keys())
            logger.info(f"摘要与以下 {len(entity_names)} 个实体关联: {entity_names[:10]}")  # 只显示前10个
            if len(entity_names) > 10:
                logger.info(f"... 还有 {len(entity_names) - 10} 个实体")
            return summary_result
        except Exception as e:
            logger.error(f"生成内容摘要失败: {e}")
            return None
    
    async def _create_news_event_from_summary(
        self, 
        summary_result: Optional[ContentSummary], 
        category: str,
        entities_count: int,
        relations_count: int,
        processed_entities: Dict[str, Entity]
    ) -> None:
        """
        从内容摘要创建新闻事件
        
        Args:
            summary_result: 内容摘要结果
            category: 内容分类
            entities_count: 实体数量
            relations_count: 关系数量
            processed_entities: 处理后的实体映射
        """
        if not summary_result or not summary_result.title:
            logger.info("摘要结果无效，跳过创建新闻事件")
            return
            
        try:
            # 验证摘要数据的有效性
            if not isinstance(summary_result.keywords, (list, tuple)):
                logger.warning(f"关键词格式异常，期望list/tuple，实际为{type(summary_result.keywords)}")
                keywords = []
            else:
                keywords = list(summary_result.keywords)
            
            news_event = NewsEvent(
                title=summary_result.title,
                content=summary_result.summary,
                source="kg_content_processor",
                publish_time=datetime.now(),
                metadata={
                    "category": category,
                    "keywords": keywords,
                    "importance_score": summary_result.importance_score or 0.0,
                    "entities_count": entities_count,
                    "relations_count": relations_count,
                    "summary_quality": "ai_generated"
                }
            )
            
            created_news = await self.store.create_news_event(news_event)
            logger.info(f"成功创建新闻事件: ID={created_news.id}, title={created_news.title}, category={category}")
            
            # 关联新闻事件与实体
            if processed_entities:
                for entity_name, entity in processed_entities.items():
                    try:
                        await self.store.add_entity_relation(created_news.id, entity.id)
                    except Exception as e:
                        logger.error(f"关联新闻事件与实体失败: news_id={created_news.id}, entity_id={entity.id}, entity_name={entity_name}, error={e}")
            
        except ValueError as e:
            logger.error(f"创建新闻事件参数验证失败: {e}")
        except ConnectionError as e:
            logger.error(f"存储连接失败，无法创建新闻事件: {e}")
        except Exception as e:
            logger.error(f"创建新闻事件时发生未知错误: {e}", exc_info=True)

    async def query_knowledge(self, query: str) -> str:
        """
        查询知识图谱
        
        Args:
            query: 查询语句
            
        Returns:
            查询结果
        """
        try:
            # 确保store已初始化
            await self._ensure_store_initialized()
            
            if not self._validate_store_initialized():
                raise RuntimeError("存储未初始化，请先调用initialize方法")
            
            self._log_operation_start("查询知识图谱", 查询=query)
            
            # 1. 向量搜索查找相关实体
            search_results = await self.store.search_entities(
                query=query,
                top_k=10,
                include_vector_search=True,
                include_full_text_search=True
            )
            
            if not search_results:
                self._log_operation_success("查询知识图谱", 结果="未找到相关知识")
                return "未找到相关知识"
            
            # 2. 构建查询上下文
            context = self._build_query_context(search_results)
            
            # 3. 使用大模型生成回答
            response = await self.generate_with_prompt(
                "query_kg",
                query=query,
                context=context
            )
            
            self._log_operation_success("知识图谱查询")
            return response
            
        except Exception as e:
            self._handle_operation_error("查询知识图谱", e)

    @staticmethod
    def _build_query_context(search_results: List) -> str:
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


