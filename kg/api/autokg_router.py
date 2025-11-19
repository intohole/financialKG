from typing import Any, Dict

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.autokg_service import AutoKGService
from ..services.database.knowledge_graph_service import KnowledgeGraphService
from ..services.news_processing_service import NewsProcessingService
from . import schemas
from .base_router import BaseRouter
from .deps import (get_autokg_service, get_db, get_knowledge_graph_service,
                   get_news_processing_service)


class AutoKGRouter(BaseRouter):
    """自动知识图谱构建路由类"""

    def __init__(self):
        super().__init__(prefix="/autokg", tags=["autokg"])
        self._register_routes()

    def _register_routes(self):
        """注册路由"""
        router = self.get_router()

        @router.post(
            "/extract-entities",
            response_model=Dict[str, Any],
            status_code=200
        )
        async def extract_entities(
            text: schemas.TextInput,
            autokg_service: AutoKGService = Depends(get_autokg_service),
        ):
            """从文本中抽取实体"""
            return await autokg_service.extract_entities(text.text)

        @router.post(
            "/extract-relations",
            response_model=Dict[str, Any],
            status_code=200
        )
        async def extract_relations(
            text: schemas.TextInput,
            autokg_service: AutoKGService = Depends(get_autokg_service),
        ):
            """从文本中抽取关系"""
            return await autokg_service.extract_relations(text.text)

        @router.post(
            "/process-text",
            response_model=Dict[str, Any],
            status_code=200
        )
        async def process_text(
            text: schemas.TextInput,
            autokg_service: AutoKGService = Depends(get_autokg_service),
        ):
            """处理文本，抽取实体和关系"""
            return await autokg_service.process_text(text.text)

        @router.post(
            "/process-news",
            response_model=schemas.NewsProcessingResponse,
            status_code=201
        )
        async def process_news(
            news: schemas.NewsCreate,
            news_processing_service: NewsProcessingService = Depends(
                get_news_processing_service
            ),
        ):
            """处理新闻，构建知识图谱"""
            news_data = news.model_dump()
            return await news_processing_service.process_and_store_news(
                news_data
            )

        @router.post(
            "/bulk-process",
            response_model=Dict[str, Any],
            status_code=200
        )
        async def bulk_process(
            data: schemas.BulkInput,
            autokg_service: AutoKGService = Depends(get_autokg_service),
        ):
            """批量处理文本，构建知识图谱"""
            # 转换为AutoKGService所需的格式
            text_list = []
            for item in data.items:
                is_model = hasattr(item, "model_dump")

                # 处理Model对象
                if is_model:
                    text = getattr(item, "text", None)
                    if text:
                        text_list.append(text)
                    else:
                        title = getattr(item, "title", "")
                        content = getattr(item, "content", "")
                        if title or content:
                            text_list.append(f"{title} {content}")

                # 处理字典对象
                else:
                    text = item.get("text", None)
                    if text:
                        text_list.append(text)
                    else:
                        title = item.get("title", "")
                        content = item.get("content", "")
                        if title or content:
                            text_list.append(f"{title} {content}")
            return await autokg_service.process_batch(text_list)

        @router.post(
            "/{news_id}/process",
            response_model=schemas.NewsProcessingResponse
        )
        async def process_news_by_id(
            news_id: int,
            llm_data: schemas.LLMExtractedData,
            kg_service: KnowledgeGraphService = Depends(
                get_knowledge_graph_service
            ),
            db: AsyncSession = Depends(get_db)
        ):
            """处理新闻"""
            processed_result = await kg_service.process_news(
                news_id, llm_data.entities, llm_data.relations
            )
            if not processed_result:
                raise ValueError("News not found or processing failed")
            return await self.handle_response(
                processed_result,
                message="新闻处理成功"
            )


# 创建路由实例
autokg_router_instance = AutoKGRouter()
autokg_router = autokg_router_instance.get_router()
