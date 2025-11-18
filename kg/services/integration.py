"""
实体关系去重合并服务集成模块

该模块提供将EntityRelationDeduplicationService集成到现有系统的功能，
包括服务注册、依赖注入和统一导出。
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from kg.services.entity_relation_deduplication_service import EntityRelationDeduplicationService
from kg.services.database.entity_service import EntityService
from kg.services.database.relation_service import RelationService
from kg.services.llm_service import LLMService
# 导入embedding和chroma服务类型
from kg.services.embedding_service import EmbeddingService
from kg.services.chroma_service import ChromaService
from kg.database.repositories import EntityRepository, RelationRepository, EntityGroupRepository, RelationGroupRepository

logger = logging.getLogger(__name__)


class DeduplicationServiceRegistry:
    """去重服务注册表，用于管理和提供EntityRelationDeduplicationService实例"""
    
    _instance: Optional[EntityRelationDeduplicationService] = None
    _registry: Dict[str, EntityRelationDeduplicationService] = {}
    
    @classmethod
    def register_service(cls, 
                        session: Session,
                        llm_service: LLMService,
                        service_id: str = "default",
                        embedding_service: Optional[EmbeddingService] = None,
                        chroma_service: Optional[ChromaService] = None) -> EntityRelationDeduplicationService:
        """
        注册去重服务实例
        
        Args:
            session: 数据库会话
            llm_service: LLM服务实例
            service_id: 服务ID，默认为"default"
            
        Returns:
            EntityRelationDeduplicationService: 去重服务实例
        """
        # 创建服务实例（EntityRelationDeduplicationService内部会自动创建所需的服务和仓库）
        service = EntityRelationDeduplicationService(
            session=session,
            llm_service=llm_service,
            embedding_service=embedding_service,
            chroma_service=chroma_service
        )
        
        # 注册服务
        cls._registry[service_id] = service
        if service_id == "default":
            cls._instance = service
        
        logger.info(f"已注册去重服务实例，服务ID: {service_id}")
        return service
    
    @classmethod
    def get_service(cls, service_id: str = "default") -> Optional[EntityRelationDeduplicationService]:
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
        return cls._instance


def create_deduplication_service_provider(
    session_factory,
    llm_service: LLMService,
    service_config: Optional[Dict[str, Any]] = None,
    embedding_service: Optional[EmbeddingService] = None,
    chroma_service: Optional[ChromaService] = None
) -> EntityRelationDeduplicationService:
    """
    创建去重服务提供者
    
    Args:
        session_factory: 数据库会话工厂
        llm_service: LLM服务实例
        service_config: 服务配置
        
    Returns:
        EntityRelationDeduplicationService: 去重服务实例
    """
    # 创建数据库会话
    session = session_factory()
    
    # 注册并获取默认服务
    service = DeduplicationServiceRegistry.register_service(
        session=session,
        llm_service=llm_service,
        service_id="default",
        embedding_service=embedding_service,
        chroma_service=chroma_service
    )
    
    return service


async def register_deduplication_tasks(scheduler=None, registry=None, session_factory=None):
    """
    注册定期去重任务到APScheduler调度器
    
    Args:
        scheduler: APScheduler的AsyncIOScheduler实例
        registry: DeduplicationServiceRegistry实例
        session_factory: 数据库会话工厂函数，用于创建新的会话
        
    Returns:
        dict: 注册的任务ID映射
    """
    task_ids = {}
    
    try:
        # 验证必要的参数
        if not scheduler:
            raise RuntimeError("未提供调度器实例")
        
        if not registry:
            raise RuntimeError("未提供去重服务注册表")
        
        # 获取默认去重服务
        service = registry.get_default_service()
        if not service:
            raise RuntimeError("未找到可用的去重服务实例")
        
        # 包装异步任务执行函数，确保任务运行时使用新的数据库会话
        async def run_with_new_session(task_func, **kwargs):
            """在新的数据库会话中运行任务"""
            # 优先使用传入的session_factory，否则尝试导入默认的
            try:
                if session_factory:
                    async with await session_factory() as new_session:
                        try:
                            # 确保服务使用新的会话
                            if hasattr(service, 'session'):
                                service.session = new_session
                            # 执行任务
                            result = await task_func(**kwargs)
                            logger.info(f"去重任务执行成功: {task_func.__name__}")
                            return result
                        except Exception as e:
                            logger.error(f"执行去重任务时出错: {str(e)}")
                            raise
                else:
                    # 尝试使用数据库管理器获取会话
                    try:
                        from kg.database import get_db_manager
                        db_manager = get_db_manager()
                        async with await db_manager.get_session() as new_session:
                            if hasattr(service, 'session'):
                                service.session = new_session
                            result = await task_func(**kwargs)
                            logger.info(f"去重任务执行成功: {task_func.__name__}")
                            return result
                    except Exception as import_error:
                        # 如果都失败了，使用现有的会话（不推荐，但作为后备方案）
                        logger.warning("无法获取新的数据库会话，使用现有会话")
                        if hasattr(service, 'session') and service.session:
                            result = await task_func(**kwargs)
                            logger.info(f"去重任务执行成功: {task_func.__name__}")
                            return result
                        else:
                            raise RuntimeError("无法获取数据库会话")
            except Exception as e:
                logger.error(f"运行任务时出错: {str(e)}")
                # 任务失败不应影响整个系统，记录错误但不抛出异常
                return {"error": str(e)}
        
        # 注册定期实体去重任务 - 每天凌晨1点执行
        entity_job = scheduler.add_job(
            run_with_new_session,
            trigger='cron',
            hour=1,
            minute=0,
            second=0,
            id='entity_deduplication_daily',
            name='每日实体去重',
            replace_existing=True,
            kwargs={
                'task_func': service.deduplicate_all_entities,
                'similarity_threshold': 0.85,
                'batch_size': 50,
                'entity_types': ['公司', '人物', '产品', '地点']
            },
            misfire_grace_time=3600,  # 允许任务延迟1小时执行
            coalesce=False,
            max_instances=3
        )
        task_ids['entity_deduplication'] = entity_job.id
        logger.info(f"已注册实体去重任务，任务ID: {entity_job.id}")
        
        # 注册定期关系去重任务 - 每天凌晨2点执行
        relation_job = scheduler.add_job(
            run_with_new_session,
            trigger='cron',
            hour=2,
            minute=0,
            second=0,
            id='relation_deduplication_daily',
            name='每日关系去重',
            replace_existing=True,
            kwargs={
                'task_func': service.deduplicate_all_relations,
                'similarity_threshold': 0.8,
                'batch_size': 50,
                'relation_types': ['控股', '投资', '合作', '竞争']
            },
            misfire_grace_time=3600,
            coalesce=False,
            max_instances=3
        )
        task_ids['relation_deduplication'] = relation_job.id
        logger.info(f"已注册关系去重任务，任务ID: {relation_job.id}")
        
        # 注册完整去重流程任务 - 每周日凌晨3点执行
        full_deduplication_job = scheduler.add_job(
            run_with_new_session,
            trigger='cron',
            hour=3,
            minute=0,
            second=0,
            day_of_week=0,  # 0表示周日
            id='full_deduplication_weekly',
            name='每周完整去重流程',
            replace_existing=True,
            kwargs={
                'task_func': service.full_deduplication,
                'similarity_threshold': 0.85,
                'batch_size': 100
            },
            misfire_grace_time=7200,
            coalesce=False,
            max_instances=2
        )
        task_ids['full_deduplication'] = full_deduplication_job.id
        logger.info(f"已注册完整去重流程任务，任务ID: {full_deduplication_job.id}")
        
        logger.info(f"成功注册所有去重定时任务，总计 {len(task_ids)} 个任务")
        
    except Exception as e:
        logger.error(f"注册去重任务失败: {str(e)}")
        raise
    
    return task_ids


# 导出公共接口
__all__ = [
    "EntityRelationDeduplicationService",
    "DeduplicationServiceRegistry",
    "create_deduplication_service_provider",
    "register_deduplication_tasks"
]
