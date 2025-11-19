import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from kg.core.config import llm_config
from kg.database.models import News
from kg.database.repositories import (EntityRepository, NewsRepository,
                                      RelationRepository)
from kg.services.database.knowledge_graph_service import KnowledgeGraphService
from kg.services.database.news_service import NewsService
from kg.services.embedding_service import ThirdPartyEmbeddingService
from kg.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class AutoKGService:
    """AutoKG服务类，整合大模型调用和实体关系提取"""

    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        llm_service: Optional[LLMService] = None,
        news_service: Optional[NewsService] = None,
        embedding_service: Optional[ThirdPartyEmbeddingService] = None,
    ):
        """初始化AutoKG服务"""
        self.llm_service = llm_service or LLMService()
        self.kg_service = kg_service
        self.news_service = news_service or self.kg_service.news_service
        self.embedding_service = embedding_service or ThirdPartyEmbeddingService()
        self.logger = logging.getLogger(self.__class__.__name__)

        # 初始化时检查大模型配置
        self._check_config()
        self.logger.info("AutoKGService初始化完成")

    def _check_config(self) -> None:
        """检查大模型配置是否正确"""
        if not llm_config.model:
            raise RuntimeError("未配置大模型名称")
        if not llm_config.api_key:
            raise RuntimeError("未配置大模型API密钥")

    async def extract_entities(
        self, text: str, entity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """从文本中提取实体"""
        logger.info(f"开始提取实体，文本长度: {len(text)}")

        result = await self.llm_service.extract_entities(text, entity_types)
        entities = result.get("entities", [])

        logger.info(f"实体提取完成，共提取到 {len(entities)} 个实体")
        return {
            "entities": entities,
            "total_entities": len(entities),
            "timestamp": datetime.now().isoformat(),
        }

    async def extract_relations(self, text: str) -> Dict[str, Any]:
        """从文本中提取关系"""
        logger.info(f"开始提取关系，文本长度: {len(text)}")

        result = await self.llm_service.extract_relations(text)
        relations = result.get("relations", [])

        logger.info(f"关系提取完成，共提取到 {len(relations)} 个关系")
        return {
            "relations": relations,
            "total_relations": len(relations),
            "timestamp": datetime.now().isoformat(),
        }

    async def extract_triples(self, text: str) -> Dict[str, Any]:
        """从文本中提取三元组"""
        logger.info(f"开始提取三元组，文本长度: {len(text)}")

        entities_result = await self.extract_entities(text)
        relations_result = await self.extract_relations(text)

        entities = entities_result.get("entities", [])
        relations = relations_result.get("relations", [])

        logger.info(
            f"三元组提取完成，实体: {len(entities)} 个，关系: {len(relations)} 个"
        )
        return {
            "entities": entities,
            "relations": relations,
            "total_entities": len(entities),
            "total_relations": len(relations),
            "timestamp": datetime.now().isoformat(),
        }

    async def process_text(self, text: str) -> Dict[str, Any]:
        """处理文本，提取实体、关系并构造三元组"""
        logger.info(f"开始处理文本，文本长度: {len(text)}")

        # 先提取实体
        entities_result = await self.llm_service.extract_entities(text)
        entities = entities_result.get("entities", [])
        logger.info(f"共提取到 {len(entities)} 个实体")

        # 再提取关系
        relations_result = await self.llm_service.extract_relations(text, entities)
        relations = relations_result.get("relations", [])
        logger.info(f"共提取到 {len(relations)} 个关系")

        # 构造三元组
        triples = []
        for relation in relations:
            source_entity = next(
                (e for e in entities if e["name"] == relation["source_entity"]), None
            )
            target_entity = next(
                (e for e in entities if e["name"] == relation["target_entity"]), None
            )
            if source_entity and target_entity:
                triples.append(
                    {
                        "source_entity": source_entity,
                        "target_entity": target_entity,
                        "relation_type": relation["relation_type"],
                        "relation_description": relation.get(
                            "relation_description", ""
                        ),
                        "confidence": relation.get("confidence", 0.0),
                    }
                )

        logger.info(f"构造完成 {len(triples)} 个三元组")
        logger.info(
            f"文本处理完成，实体: {len(entities)} 个，关系: {len(relations)} 个"
        )
        return {
            "entities": entities,
            "relations": relations,
            "triples": triples,
            "total_entities": len(entities),
            "total_relations": len(relations),
            "timestamp": datetime.now().isoformat(),
        }

    async def process_and_store_text(self, text: str) -> Dict[str, Any]:
        """处理文本并将提取的知识存储到知识图谱"""
        logger.info(f"开始处理并存储文本，文本长度: {len(text)}")

        # 提取知识
        result = await self.process_text(text)

        # 存储到知识图谱
        entities = result.get("entities", [])
        relations = result.get("relations", [])

        stored_entities = []
        stored_relations = []

        if entities:
            stored_entities = await self.kg_service.bulk_add_entities(entities)
            logger.info(f"已存储 {len(stored_entities)} 个实体到知识图谱")

        if relations:
            stored_relations = await self.kg_service.bulk_add_relations(relations)
            logger.info(f"已存储 {len(stored_relations)} 个关系到知识图谱")

        logger.info(f"文本处理和存储完成")
        return {
            "entities": stored_entities,
            "relations": stored_relations,
            "total_entities": len(stored_entities),
            "total_relations": len(stored_relations),
            "timestamp": datetime.now().isoformat(),
        }

    async def process_batch(self, texts: List[str]) -> Dict[str, Any]:
        """
        批量处理文本，抽取实体和关系

        Args:
            texts: 待处理文本列表

        Returns:
            Dict[str, Any]: 处理结果
        """
        logger.info(f"开始批量处理 {len(texts)} 个文本")

        results = []
        total_entities = 0
        total_relations = 0
        total_triples = 0

        for text in texts:
            result = await self.process_text(text)
            results.append(result)
            total_entities += len(result.get("entities", []))
            total_relations += len(result.get("relations", []))
            total_triples += len(result.get("triples", []))

        logger.info(f"批量处理完成，共处理 {len(texts)} 个文本")

        return {
            "results": results,
            "total_texts": len(texts),
            "total_entities": total_entities,
            "total_relations": total_relations,
            "total_triples": total_triples,
            "timestamp": datetime.now().isoformat(),
        }

    async def process_news(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理新闻，提取实体和关系并存储到数据库"""
        logger.info(f"开始处理新闻，标题: {news_data.get('title', '无标题')}")

        # 存储新闻到数据库
        news_repo = NewsRepository()
        news = await news_repo.save(**news_data)
        logger.info(f"新闻已存储到数据库，ID: {news.id}")

        # 提取知识
        text = news_data.get("title", "") + " " + news_data.get("content", "")
        knowledge_result = await self.process_text(text)

        # 存储到知识图谱
        entities = knowledge_result.get("entities", [])
        relations = knowledge_result.get("relations", [])

        if entities or relations:
            await self.kg_service.bulk_add_entities(entities)
            await self.kg_service.bulk_add_relations(relations)
            logger.info(
                f"新闻知识已存储到知识图谱，实体: {len(entities)} 个，关系: {len(relations)} 个"
            )

        logger.info(f"新闻处理完成")
        return {
            "news_id": news.id,
            "entities": entities,
            "relations": relations,
            "total_entities": len(entities),
            "total_relations": len(relations),
            "timestamp": datetime.now().isoformat(),
        }

    async def bulk_process_texts(self, texts: List[str]) -> Dict[str, Any]:
        """批量处理文本，提取实体和关系"""
        logger.info(f"开始批量处理文本，共 {len(texts)} 条")

        results = []
        total_entities = 0
        total_relations = 0

        for i, text in enumerate(texts):
            try:
                result = await self.process_text(text)
                results.append({"index": i, "result": result, "success": True})
                total_entities += result.get("total_entities", 0)
                total_relations += result.get("total_relations", 0)
            except Exception as e:
                results.append({"index": i, "error": str(e), "success": False})
                logger.error(f"批量处理文本失败，索引: {i}，错误: {e}")

        logger.info(
            f"批量处理文本完成，共处理 {len(results)} 条，实体: {total_entities} 个，关系: {total_relations} 个"
        )
        return {
            "results": results,
            "total_processed": len(results),
            "total_entities": total_entities,
            "total_relations": total_relations,
            "timestamp": datetime.now().isoformat(),
        }

    async def bulk_process_and_store_texts(self, texts: List[str]) -> Dict[str, Any]:
        """批量处理文本并存储到知识图谱"""
        logger.info(f"开始批量处理并存储文本，共 {len(texts)} 条")

        results = []
        total_entities = 0
        total_relations = 0

        for i, text in enumerate(texts):
            try:
                result = await self.process_and_store_text(text)
                results.append({"index": i, "result": result, "success": True})
                total_entities += result.get("total_entities", 0)
                total_relations += result.get("total_relations", 0)
            except Exception as e:
                results.append({"index": i, "error": str(e), "success": False})
                logger.error(f"批量处理并存储文本失败，索引: {i}，错误: {e}")

        logger.info(
            f"批量处理并存储文本完成，共处理 {len(results)} 条，实体: {total_entities} 个，关系: {total_relations} 个"
        )
        return {
            "results": results,
            "total_processed": len(results),
            "total_entities": total_entities,
            "total_relations": total_relations,
            "timestamp": datetime.now().isoformat(),
        }
