"""去重相关路由"""

from fastapi import Depends
from typing import Dict, Any

from ..interfaces.deduplication_service import DeduplicationConfig
from . import schemas
from .deps import get_entity_relation_deduplication_service
from .base_router import BaseRouter

# 创建去重路由类
class DeduplicationRouter(BaseRouter):
    """去重路由类"""
    
    def __init__(self):
        super().__init__(prefix="/deduplication", tags=["deduplication"])
        self._register_routes()
    
    def _register_routes(self):
        """注册路由"""
        router = self.get_router()
        
        # 执行实体和关系去重端点
        @router.post("/run", response_model=schemas.DeduplicationResult)
        async def run_deduplication(
            config: schemas.DeduplicationConfigRequest,
            deduplication_service = Depends(get_entity_relation_deduplication_service)
        ):
            """
            执行自动化去重操作
            
            根据配置自动处理实体或关系的去重，支持按类型、关键词等多种过滤方式，
            并根据配置自动执行合并操作
            """
            try:
                # 转换请求配置为服务配置
                dedup_config = DeduplicationConfig(
                    similarity_threshold=config.similarity_threshold,
                    batch_size=config.batch_size,
                    limit=config.limit,
                    entity_types=config.entity_types,
                    keyword=config.keyword,
                    auto_merge=config.auto_merge,
                    use_vector_search=config.use_vector_search,
                    fallback_to_string_similarity=config.fallback_to_string_similarity,
                    min_entities_for_duplication=config.min_entities_for_duplication
                )
                
                result = await deduplication_service.deduplicate(dedup_config)
                return await self.handle_response(result.to_dict(), message="去重操作执行成功")
            except ValueError as e:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                from ..utils.exception_handlers import handle_generic_exception
                raise handle_generic_exception(e, self.logger, "执行去重操作")
        
        # 获取去重统计信息端点
        @router.get("/stats", response_model=Dict[str, Any])
        async def get_deduplication_statistics(
            deduplication_service = Depends(get_entity_relation_deduplication_service)
        ):
            """
            获取系统去重统计信息
            """
            try:
                stats = await deduplication_service.get_deduplication_stats()
                return await self.handle_response(stats, message="获取去重统计信息成功")
            except Exception as e:
                from ..utils.exception_handlers import handle_generic_exception
                raise handle_generic_exception(e, self.logger, "获取去重统计信息")


# 创建路由实例
deduplication_router_instance = DeduplicationRouter()
deduplication_router = deduplication_router_instance.get_router()