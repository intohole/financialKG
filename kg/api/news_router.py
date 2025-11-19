from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from ..services.database.knowledge_graph_service import KnowledgeGraphService
from ..services.news_processing_service import NewsProcessingService
from . import schemas
from .deps import get_db, get_knowledge_graph_service, get_news_processing_service
from .base_router import BaseRouter

# 日志记录器通过BaseRouter继承

# 创建新闻路由类
class NewsRouter(BaseRouter):
    """新闻路由类"""
    
    def __init__(self):
        super().__init__(prefix="/news", tags=["news"])
        self._register_routes()
    
    def _register_routes(self):
        """注册路由"""
        router = self.get_router()
        
        @router.post("", response_model=schemas.News, status_code=201)
        async def create_news(
            news: schemas.NewsCreate,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db)
        ):
            """创建新闻"""
            return await self.handle_create(
                db=db,
                create_data=news.model_dump(),
                service_method=kg_service.create_news,
                response_model=schemas.News
            )
        
        @router.get("/{news_id}", response_model=schemas.News)
        async def get_news(
            news_id: int,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db)
        ):
            """获取单个新闻"""
            return await self.handle_get(
                db=db,
                item_id=news_id,
                service_method=kg_service.get_news_by_id,
                response_model=schemas.News
            )
        
        @router.get("", response_model=List[schemas.News])
        async def get_all_news(
            source: Optional[str] = None,
            category: Optional[str] = None,
            page: int = 1,
            page_size: int = 10,
            sort_by: Optional[str] = None,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db)
        ):
            """获取新闻列表"""
            return await self.handle_list(
                db=db,
                service_method=kg_service.get_news,
                response_model=schemas.News,
                source=source,
                category=category,
                page=page,
                page_size=page_size,
                order_by=sort_by
            )
        
        @router.post("/{news_id}/process", response_model=schemas.NewsProcessingResponse)
        async def process_news(
            news_id: int,
            llm_data: schemas.LLMExtractedData,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db)
        ):
            """处理新闻"""
            try:
                processed_result = await kg_service.process_news(news_id, llm_data.entities, llm_data.relations)
                if not processed_result:
                    raise ValueError("News not found or processing failed")
                return await self.handle_response(processed_result, message="新闻处理成功")
            except ValueError as e:
                from ..utils.exception_handlers import handle_value_error
                raise handle_value_error(e, self.logger)
            except Exception as e:
                from ..utils.exception_handlers import handle_generic_exception
                raise handle_generic_exception(e, self.logger, "处理新闻")
        
        @router.post("/process", response_model=schemas.NewsProcessingResponse)
        async def process_news_with_llm(
            request: schemas.NewsProcessingRequest,
            news_processing_service: NewsProcessingService = Depends(get_news_processing_service)
        ):
            """
            处理新闻并使用LLM提取实体、关系和生成摘要
            
            - **title**: 新闻标题
            - **content**: 新闻内容
            - **source_url**: 新闻来源URL
            - **publish_date**: 发布日期（ISO格式字符串）
            - **source**: 新闻来源
            - **author**: 作者
            """
            try:
                # 将请求模型转换为字典，以便传递给服务
                news_data = request.model_dump()
                
                # 调用新闻处理服务
                result = await news_processing_service.process_and_store_news(news_data)
                
                return await self.handle_response(result, message="LLM处理新闻成功")
            except ValueError as e:
                from ..utils.exception_handlers import handle_value_error
                raise handle_value_error(e, self.logger)
            except RuntimeError as e:
                from ..utils.exception_handlers import handle_runtime_error
                raise handle_runtime_error(e, self.logger)
            except Exception as e:
                from ..utils.exception_handlers import handle_generic_exception
                raise handle_generic_exception(e, self.logger, "LLM处理新闻")


# 创建路由实例
news_router_instance = NewsRouter()
news_router = news_router_instance.get_router()
