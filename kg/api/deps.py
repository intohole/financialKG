import logging

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import db_session
from ..services.autokg_service import AutoKGService
from ..services.database.knowledge_graph_service import KnowledgeGraphService
from ..services.entity_relation_deduplication_service import \
    EntityRelationDeduplicationService
from ..services.llm.entity_extraction import EntityExtractionService
from ..services.llm.relation_extraction import RelationExtractionService
from ..services.news_processing_service import NewsProcessingService


# 配置通用日志记录器
def get_logger(name: str = "api") -> logging.Logger:
    """获取配置好的日志记录器"""
    logger = logging.getLogger(name)
    return logger


# 数据库会话依赖
async def get_db():
    """获取数据库会话"""
    async with db_session() as session:
        yield session


# KnowledgeGraphService依赖
async def get_kg_service(db: AsyncSession = Depends(get_db)) -> KnowledgeGraphService:
    """获取知识图谱服务实例"""
    return KnowledgeGraphService(db)


# 为了兼容entities_router中的导入，添加别名
get_knowledge_graph_service = get_kg_service


# EntityRelationDeduplicationService依赖
async def get_entity_relation_deduplication_service(
    request: Request,
) -> EntityRelationDeduplicationService:
    """从请求中获取实体关系去重服务实例"""
    if not hasattr(request.app.state, "deduplication_service"):
        raise HTTPException(status_code=500, detail="去重服务未初始化")
    return request.app.state.deduplication_service


# NewsProcessingService依赖
async def get_news_processing_service(
    kg_service: KnowledgeGraphService = Depends(get_kg_service),
) -> NewsProcessingService:
    """获取新闻处理服务实例"""
    return NewsProcessingService(data_services=kg_service)


# EntityExtractionService依赖
async def get_entity_extraction_service() -> EntityExtractionService:
    """获取实体抽取服务实例"""
    return EntityExtractionService()


# RelationExtractionService依赖
async def get_relation_extraction_service() -> RelationExtractionService:
    """获取关系抽取服务实例"""
    return RelationExtractionService()


# AutoKGService依赖
async def get_autokg_service(db: AsyncSession = Depends(get_db)) -> AutoKGService:
    """获取AutoKG服务实例"""
    return AutoKGService(kg_service=KnowledgeGraphService(db))
