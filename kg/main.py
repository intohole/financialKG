"""
金融知识图谱服务主入口

此模块负责初始化和配置FastAPI应用程序，设置中间件，初始化核心服务，
并注册API路由。作为系统的主要入口点，它协调各组件间的交互并确保服务
能够正常启动和运行。
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入核心配置和服务
from kg.database import init_database

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

# 只保留必要的全局变量

@app.on_event("startup")
async def initialize_services():
    """初始化所有服务"""
    
    try:
        logger.info("应用正在启动...")
        
        # 初始化数据库表
        logger.info("正在初始化数据库表...")
        await db_manager.create_tables_async()
        logger.info("数据库表初始化完成")
        
        # 初始化其他服务暂时跳过
        logger.info("应用启动完成")
    except Exception as e:
        logger.error(f"服务初始化失败: {str(e)}")
        raise

# 包含API路由
# 这里注册了系统的所有API端点，包括实体管理、关系管理、新闻处理和去重功能
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

# 健康检查端点
@app.get("/health")
async def health_check():
    """
    系统健康检查端点
    
    用于监控系统运行状态，返回系统当前的运行情况信息
    可以被负载均衡器、监控系统等外部服务调用
    """
    return {"status": "ok", "message": "Financial Knowledge Graph Service is running"}

# 路由注册前的空白区域

# 包含所有路由
include_routers(app)

if __name__ == "__main__":
    import uvicorn
    import sys
    # 允许通过命令行参数指定端口
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].startswith("--port"):
        try:
            port = int(sys.argv[1].split("=")[1]) if "=" in sys.argv[1] else int(sys.argv[2])
        except (IndexError, ValueError):
            print(f"Invalid port argument: {sys.argv[1]}, using default port 8000")
    uvicorn.run("kg.main:app", host="0.0.0.0", port=port, reload=True)