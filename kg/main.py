"""
金融知识图谱服务主入口

此模块负责初始化和配置FastAPI应用程序，设置中间件，初始化核心服务，
并注册API路由。作为系统的主要入口点，它协调各组件间的交互并确保服务
能够正常启动和运行。
"""

import logging

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, FileResponse

# 导入新的配置系统
from kg.core.config_simple import config
# 导入核心服务
from kg.database import init_database

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format=config.LOG_FORMAT,
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title=config.app.APP_NAME,
    description=config.app.APP_DESCRIPTION,
    version=config.app.APP_VERSION,
    debug=True,
)

# 添加请求压缩中间件
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # 只压缩大于1KB的响应
)


# 性能监控中间件
@app.middleware("http")
async def performance_monitor(request: Request, call_next):
    """记录请求处理时间"""
    import time

    start_time = time.time()
    response = await call_next(request)
    end_time = time.time()

    process_time = end_time - start_time

    # 记录慢请求
    if process_time > 1.0:  # 记录处理时间超过1秒的请求
        logger.warning(
            f"慢请求: {request.method} {request.url} 耗时: {process_time:.2f}秒"
        )

    # 在响应头中添加处理时间
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 只保留必要的全局变量

# 初始化数据库管理器（延迟初始化）
db_manager = init_database()


# 全局错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    status_code = getattr(exc, "status_code", 500)
    if status_code not in [400, 401, 403, 404, 405, 500]:
        status_code = 500

    logger.error(f"请求异常: {str(exc)}")

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "message": str(exc),
            "code": status_code,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "code": exc.status_code,
        },
    )


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
        
        # 打印所有注册的路由信息
        logger.info("已注册的路由信息:")
        for route in app.routes:
            methods = " ".join(sorted(route.methods)) if hasattr(route, "methods") else "N/A"
            logger.info(f"  {methods} {route.path}")
            
        logger.info("应用启动完成")
    except Exception as e:
        logger.error(f"服务初始化失败: {str(e)}")
        raise


# 包含API路由
# 这里注册了系统的所有API端点，包括实体管理、关系管理、新闻处理和去重功能
from kg.api import include_routers
include_routers(app)


# 挂载静态文件
app.mount("/", StaticFiles(directory="kg/static", html=True), name="static")

# 添加根路径（备用）
@app.get("/api")
async def api_root():
    """API根路径，提供基本信息"""
    return {"message": "欢迎使用知识图谱API", "version": "1.0.0", "docs": "/docs"}


# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.CORS_ORIGINS,
    allow_credentials=config.cors.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.cors.CORS_ALLOW_METHODS,
    allow_headers=config.cors.CORS_ALLOW_HEADERS,
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
    import sys

    import uvicorn

    # 允许通过命令行参数覆盖配置
    host = config.app.HOST
    port = config.app.PORT
    reload = config.app.RELOAD

    # 处理命令行参数
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith("--host"):
            if "=" in arg:
                host = arg.split("=")[1]
            elif i + 1 < len(sys.argv):
                host = sys.argv[i + 1]
                i += 1
        elif arg.startswith("--port"):
            if "=" in arg:
                try:
                    port = int(arg.split("=")[1])
                except ValueError:
                    pass
            elif i + 1 < len(sys.argv):
                try:
                    port = int(sys.argv[i + 1])
                except ValueError:
                    pass
                i += 1
        elif arg.startswith("--reload"):
            reload = True
        i += 1

    logger.info(f"启动服务: http://{host}:{port}")
    uvicorn.run("kg.main:app", host=host, port=port, reload=reload)
