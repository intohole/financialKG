"""去重相关路由"""

from typing import Any, Dict

from fastapi import Depends

from ..interfaces.deduplication_service import DeduplicationConfig
from ..utils.exception_handlers import (handle_generic_exception,
                                        handle_value_error)
from . import schemas
from .base_router import BaseRouter
from .deps import get_entity_relation_deduplication_service


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
            deduplication_service=Depends(get_entity_relation_deduplication_service),
        ):
            """
            执行自动化去重操作

            根据配置自动处理实体或关系的去重，支持按类型、关键词等多种过滤方式，
            并根据配置自动执行合并操作

            参数:
            - config: 去重配置对象
                - similarity_threshold: 相似度阈值 (0.0-1.0)
                - batch_size: 批处理大小 (1-1000)
                - limit: 处理限制 (可选)
                - entity_types: 实体类型过滤 (可选)
                - keyword: 关键词过滤 (可选)
                - auto_merge: 是否自动合并 (默认: False)
                - use_vector_search: 是否使用向量搜索 (默认: True)
                - fallback_to_string_similarity: 是否回退到字符串相似度 (默认: True)
                - min_entities_for_duplication: 进行重复检测的最小实体数 (默认: 2)

            返回:
            - DeduplicationResult: 去重结果对象
            """
            try:
                # 转换请求配置为服务配置
                dedup_config = DeduplicationConfig(**config.model_dump())

                result = await deduplication_service.deduplicate(dedup_config)
                return await self.handle_response(
                    result.to_dict(), message="去重操作执行成功"
                )
            except ValueError as e:
                raise handle_value_error(e, self.logger)
            except Exception as e:
                raise handle_generic_exception(e, self.logger, "执行去重操作")

        # 获取去重统计信息端点
        @router.get("/stats", response_model=Dict[str, Any])
        async def get_deduplication_statistics(
            deduplication_service=Depends(get_entity_relation_deduplication_service),
        ):
            """
            获取系统去重统计信息

            返回系统的去重统计信息，包括：
            - last_run: 上次去重时间
            - success: 上次去重是否成功
            - total_processed: 处理的总数量
            - total_duplicate_groups: 去重的组数
            - total_duplicates_merged: 合并的重复项数量
            - entity_deduplication: 实体去重详细信息
            - relation_deduplication: 关系去重详细信息
            - message: 统计信息说明
            """
            try:
                stats = await deduplication_service.get_deduplication_stats()
                return await self.handle_response(stats, message="获取去重统计信息成功")
            except Exception as e:
                raise handle_generic_exception(e, self.logger, "获取去重统计信息")


# 创建路由实例
deduplication_router_instance = DeduplicationRouter()
deduplication_router = deduplication_router_instance.get_router()
