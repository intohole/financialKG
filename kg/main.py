"""
知识图谱服务主入口
"""
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 修复导入路径 - 使用正确的数据库模块路径
from kg.core.config import BaseConfig
from kg.database import init_database
from kg.services.llm_service import LLMService
from kg.services.integration import (
    DeduplicationServiceRegistry,
    create_deduplication_service_provider,
    register_deduplication_tasks
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化数据库管理器
logger.info("正在初始化数据库管理器...")
db_manager = init_database()
logger.info("数据库管理器初始化完成")

# 创建FastAPI应用实例
app = FastAPI(
    title="知识图谱API",
    description="知识图谱数据管理和查询服务",
    version="1.0.0"
)

# 全局配置和服务实例
config = BaseConfig()
llm_service = None
deduplication_service_registry = None
app.state.scheduler = None

async def initialize_services():
    """初始化所有服务"""
    global llm_service, deduplication_service_registry
    
    try:
        # 初始化数据库表
        logger.info("正在初始化数据库表...")
        await db_manager.create_tables_async()
        logger.info("数据库表初始化完成")
        
        # 初始化LLM服务
        logger.info("正在初始化LLM服务...")
        llm_service = LLMService()
        # 有些LLM服务可能不需要显式初始化
        if hasattr(llm_service, 'initialize'):
            await llm_service.initialize()
        logger.info("LLM服务初始化完成")
        
        # 初始化去重服务
        logger.info("正在初始化去重服务...")
        deduplication_service_registry = DeduplicationServiceRegistry()
        
        # 创建去重服务提供者 - 使用db_manager获取会话
        provider = create_deduplication_service_provider(
            session_factory=db_manager.get_session,
            llm_service=llm_service
        )
        
        # 注册去重服务
        deduplication_service_registry.register_provider(provider)
        logger.info("去重服务初始化完成")
        
        # 初始化任务调度器和去重定时任务
        logger.info("正在初始化任务调度器...")
        try:
            # 尝试导入APScheduler
            try:
                from apscheduler.schedulers.asyncio import AsyncIOScheduler
                from apscheduler.executors.asyncio import AsyncIOExecutor
                from apscheduler.jobstores.memory import MemoryJobStore
                
                # 创建调度器配置
                jobstores = {'default': MemoryJobStore()}
                executors = {'default': AsyncIOExecutor()}
                job_defaults = {
                    'coalesce': False,
                    'max_instances': 3
                }
                
                # 创建并启动调度器
                scheduler = AsyncIOScheduler(
                    jobstores=jobstores,
                    executors=executors,
                    job_defaults=job_defaults,
                    timezone="Asia/Shanghai"
                )
                scheduler.start()
                app.state.scheduler = scheduler
                logger.info("任务调度器启动成功")
                
                # 获取默认去重服务
                service = deduplication_service_registry.get_default_service()
                if service:
                    # 为去重任务创建简单的包装器，确保任务能正常运行
                    async def deduplicate_entities_wrapper():
                        """实体去重任务包装器"""
                        try:
                            async with await db_manager.get_session() as session:
                                # 确保服务使用新会话
                                if hasattr(service, 'session'):
                                    service.session = session
                                logger.info("开始执行实体去重任务...")
                                result = await service.deduplicate_all_entities(
                                    similarity_threshold=0.85,
                                    batch_size=50,
                                    entity_types=["公司", "人物", "产品", "地点"]
                                )
                                logger.info(f"实体去重任务执行完成: {result}")
                        except Exception as e:
                            logger.error(f"执行实体去重任务时出错: {str(e)}")
                    
                    async def deduplicate_relations_wrapper():
                        """关系去重任务包装器"""
                        try:
                            async with await db_manager.get_session() as session:
                                if hasattr(service, 'session'):
                                    service.session = session
                                logger.info("开始执行关系去重任务...")
                                result = await service.deduplicate_all_relations(
                                    similarity_threshold=0.8,
                                    batch_size=50,
                                    relation_types=["控股", "投资", "合作", "竞争"]
                                )
                                logger.info(f"关系去重任务执行完成: {result}")
                        except Exception as e:
                            logger.error(f"执行关系去重任务时出错: {str(e)}")
                    
                    # 注册去重定时任务
                    scheduler.add_job(
                        deduplicate_entities_wrapper,
                        'cron',
                        hour=1,
                        minute=0,
                        id='entity_deduplication_daily',
                        name='每日实体去重',
                        replace_existing=True
                    )
                    scheduler.add_job(
                        deduplicate_relations_wrapper,
                        'cron',
                        hour=2,
                        minute=0,
                        id='relation_deduplication_daily',
                        name='每日关系去重',
                        replace_existing=True
                    )
                    logger.info("去重定时任务注册成功")
                else:
                    logger.warning("未找到默认去重服务，跳过任务注册")
                    
            except ImportError:
                logger.warning("APScheduler 库未安装，去重定时任务不可用")
                logger.info("请安装 APScheduler: pip install apscheduler")
        except Exception as scheduler_error:
            logger.error(f"初始化调度器或注册任务失败: {str(scheduler_error)}")
            
        # 存储服务实例到app.state
        app.state.llm_service = llm_service
        app.state.deduplication_service = deduplication_service_registry.get_default_service()
        app.state.deduplication_registry = deduplication_service_registry
        
    except Exception as e:
        logger.error(f"初始化服务过程中发生错误: {str(e)}")
        # 即使出错也要确保服务能继续运行

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("应用正在启动...")
    await initialize_services()
    logger.info("应用启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    global llm_service
    logger.info("应用正在关闭...")
    
    # 关闭调度器
    if hasattr(app.state, 'scheduler') and app.state.scheduler:
        try:
            app.state.scheduler.shutdown()
            logger.info("任务调度器已关闭")
        except Exception as e:
            logger.error(f"关闭调度器时出错: {str(e)}")
    
    # 关闭LLM服务
    if llm_service and hasattr(llm_service, 'shutdown'):
        try:
            await llm_service.shutdown()
            logger.info("LLM服务已关闭")
        except Exception as e:
            logger.error(f"关闭LLM服务时出错: {str(e)}")
    
    logger.info("应用已关闭")

# 包含路由
from kg.api import include_routers

# 添加根路径
@app.get("/")
async def root():
    """根路径，提供基本信息"""
    return {
        "message": "欢迎使用知识图谱API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含所有路由
include_routers(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("kg.main:app", host="0.0.0.0", port=8000, reload=True)