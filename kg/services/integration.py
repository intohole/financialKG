"""
实体关系去重合并服务集成模块

该模块提供将EntityRelationDeduplicationService集成到现有系统的功能，
包括服务注册、依赖注入和任务调度。
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from kg.services.chroma_service import ChromaService
from kg.services.embedding_service import ThirdPartyEmbeddingService
# 导入必要的服务和类型
from kg.services.entity_relation_deduplication_service import \
    EntityRelationDeduplicationService
from kg.services.llm_service import LLMService
# 导入错误处理装饰器
from kg.utils import handle_errors

logger = logging.getLogger(__name__)


class DeduplicationServiceRegistry:
    """去重服务注册表，用于管理和提供EntityRelationDeduplicationService实例"""

    # 使用线程安全的服务存储
    _registry: Dict[str, EntityRelationDeduplicationService] = {}
    _default_service_id = "default"

    @classmethod
    @handle_errors(log_error=True, log_message="注册去重服务失败: {error}")
    def register_service(
        cls,
        session: Session,
        llm_service: LLMService,
        service_id: str = _default_service_id,
        embedding_service: Optional[ThirdPartyEmbeddingService] = None,
        chroma_service: Optional[ChromaService] = None,
    ) -> EntityRelationDeduplicationService:
        """
        注册去重服务实例

        Args:
            session: 数据库会话
            llm_service: LLM服务实例
            service_id: 服务ID，默认为"default"
            embedding_service: 嵌入服务实例
            chroma_service: Chroma服务实例

        Returns:
            EntityRelationDeduplicationService: 去重服务实例
        """
        # 创建服务实例
        service = EntityRelationDeduplicationService(
            session=session,
            llm_service=llm_service,
            embedding_service=embedding_service,
            chroma_service=chroma_service,
        )

        # 注册服务
        cls._registry[service_id] = service

        # 初始化服务
        async def _initialize_service():
            await service.initialize()

        # 尝试异步初始化服务
        try:
            import asyncio

            if not asyncio.get_event_loop().is_running():
                asyncio.run(_initialize_service())
            else:
                asyncio.create_task(_initialize_service())
        except Exception as init_error:
            logger.warning(f"异步初始化服务失败，但不影响服务注册: {init_error}")

        logger.info(f"已注册去重服务实例，服务ID: {service_id}")
        return service

    @classmethod
    def get_service(
        cls, service_id: str = _default_service_id
    ) -> Optional[EntityRelationDeduplicationService]:
        """
        获取去重服务实例

        Args:
            service_id: 服务ID，默认为"default"

        Returns:
            Optional[EntityRelationDeduplicationService]: 去重服务实例，如果不存在则返回None
        """
        return cls._registry.get(service_id)

    @classmethod
    def get_default_service(cls) -> Optional[EntityRelationDeduplicationService]:
        """
        获取默认去重服务实例

        Returns:
            Optional[EntityRelationDeduplicationService]: 默认去重服务实例
        """
        return cls.get_service(cls._default_service_id)

    @classmethod
    def unregister_service(cls, service_id: str) -> bool:
        """
        注销去重服务实例

        Args:
            service_id: 服务ID

        Returns:
            bool: 是否成功注销
        """
        if service_id in cls._registry:
            del cls._registry[service_id]
            logger.info(f"已注销去重服务实例，服务ID: {service_id}")
            return True
        return False


@handle_errors(log_error=True, log_message="创建去重服务提供者失败: {error}")
def create_deduplication_service_provider(
    session_factory,
    llm_service: LLMService,
    service_config: Optional[Dict[str, Any]] = None,
    embedding_service: Optional[ThirdPartyEmbeddingService] = None,
    chroma_service: Optional[ChromaService] = None,
) -> EntityRelationDeduplicationService:
    """
    创建去重服务提供者

    Args:
        session_factory: 数据库会话工厂
        llm_service: LLM服务实例
        service_config: 服务配置（可选）
        embedding_service: 嵌入服务实例（可选）
        chroma_service: Chroma服务实例（可选）

    Returns:
        EntityRelationDeduplicationService: 去重服务实例
    """
    # 创建数据库会话
    try:
        session = session_factory()
    except Exception as e:
        logger.error(f"创建数据库会话失败: {str(e)}")
        raise RuntimeError(f"无法创建数据库会话: {str(e)}") from e

    # 使用配置（如果提供）
    service_id = (
        service_config.get("service_id", "default") if service_config else "default"
    )

    # 注册并获取服务
    return DeduplicationServiceRegistry.register_service(
        session=session,
        llm_service=llm_service,
        service_id=service_id,
        embedding_service=embedding_service,
        chroma_service=chroma_service,
    )


@handle_errors(log_error=True, log_message="注册去重任务失败: {error}")
async def register_deduplication_tasks(
    scheduler=None,
    registry=None,
    session_factory=None,
    task_configs: Optional[Dict[str, Dict[str, Any]]] = None,
):
    """
    注册定期去重任务到APScheduler调度器

    Args:
        scheduler: APScheduler的AsyncIOScheduler实例
        registry: DeduplicationServiceRegistry实例
        session_factory: 数据库会话工厂函数，用于创建新的会话
        task_configs: 自定义任务配置，用于覆盖默认设置

    Returns:
        dict: 注册的任务ID映射
    """
    # 验证必要的参数
    if not scheduler:
        raise ValueError("调度器实例不能为空")

    if not registry:
        raise ValueError("去重服务注册表不能为空")

    # 获取默认去重服务
    service = registry.get_default_service()
    if not service:
        raise RuntimeError("未找到可用的去重服务实例")

    # 定义默认任务配置
    default_task_configs = {
        "entity_deduplication": {
            "trigger": "cron",
            "hour": 1,
            "minute": 0,
            "second": 0,
            "id": "entity_deduplication_daily",
            "name": "每日实体去重",
            "task_func": "deduplicate_all_entities",
            "kwargs": {
                "similarity_threshold": 0.85,
                "batch_size": 50,
                "entity_types": ["公司", "人物", "产品", "地点"],
            },
            "misfire_grace_time": 3600,
            "coalesce": False,
            "max_instances": 3,
        },
        "relation_deduplication": {
            "trigger": "cron",
            "hour": 2,
            "minute": 0,
            "second": 0,
            "id": "relation_deduplication_daily",
            "name": "每日关系去重",
            "task_func": "deduplicate_all_relations",
            "kwargs": {
                "similarity_threshold": 0.8,
                "batch_size": 50,
                "relation_types": ["控股", "投资", "合作", "竞争"],
            },
            "misfire_grace_time": 3600,
            "coalesce": False,
            "max_instances": 3,
        },
        "full_deduplication": {
            "trigger": "cron",
            "hour": 3,
            "minute": 0,
            "second": 0,
            "day_of_week": 0,  # 0表示周日
            "id": "full_deduplication_weekly",
            "name": "每周完整去重流程",
            "task_func": "full_deduplication",
            "kwargs": {"similarity_threshold": 0.85, "batch_size": 100},
            "misfire_grace_time": 7200,
            "coalesce": False,
            "max_instances": 2,
        },
    }

    # 合并自定义配置（如果提供）
    if task_configs:
        for task_name, config in task_configs.items():
            if task_name in default_task_configs:
                default_task_configs[task_name].update(config)

    # 包装异步任务执行函数
    async def run_with_new_session(task_func_name, **kwargs):
        """在新的数据库会话中运行任务"""
        try:
            # 获取任务函数
            task_func = getattr(service, task_func_name, None)
            if not task_func or not callable(task_func):
                raise AttributeError(f"服务没有名为'{task_func_name}'的可调用方法")

            # 尝试获取新的数据库会话
            new_session = None
            try:
                if session_factory:
                    new_session = await session_factory()
                else:
                    # 尝试使用数据库管理器获取会话
                    try:
                        from kg.database import get_db_manager

                        db_manager = get_db_manager()
                        new_session = await db_manager.get_session()
                    except ImportError:
                        logger.warning("无法导入数据库管理器")
            except Exception as e:
                logger.warning(f"获取新数据库会话失败: {str(e)}")

            # 保存原会话以便恢复
            original_session = getattr(service, "session", None)

            try:
                # 如果获取到新会话，则使用新会话
                if new_session and hasattr(service, "session"):
                    service.session = new_session

                # 执行任务
                result = await task_func(**kwargs)
                logger.info(f"去重任务执行成功: {task_func_name}")
                return result
            finally:
                # 恢复原会话
                if new_session and hasattr(service, "session"):
                    service.session = original_session

                # 关闭新会话
                if new_session:
                    try:
                        await new_session.close()
                    except:
                        pass
        except Exception as e:
            logger.error(f"运行任务时出错: {task_func_name}, 错误: {str(e)}")
            return {"error": str(e)}

    # 注册任务
    task_ids = {}
    for task_name, config in default_task_configs.items():
        try:
            # 提取任务函数名称
            task_func_name = config.pop("task_func")
            task_kwargs = config.pop("kwargs")

            # 添加任务
            job = scheduler.add_job(
                run_with_new_session,
                replace_existing=True,
                **config,
                args=[task_func_name],
                kwargs=task_kwargs,
            )

            task_ids[task_name] = job.id
            logger.info(f"已注册去重任务: {config['name']}，任务ID: {job.id}")
        except Exception as e:
            logger.error(f"注册任务 {task_name} 失败: {str(e)}")
            # 继续注册其他任务，不因单个任务失败而中断

    logger.info(f"成功注册 {len(task_ids)} 个去重定时任务")
    return task_ids


# 导出公共接口
__all__ = [
    "DeduplicationServiceRegistry",
    "create_deduplication_service_provider",
    "register_deduplication_tasks",
]
