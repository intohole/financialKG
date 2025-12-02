"""FastAPI应用程序主文件

提供知识图谱的多类别支持API服务
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# from app.api.routes import router as knowledge_graph_router  # 该模块不存在
from app.api.kg_query_routes import register_routes as register_kg_query_routes
from app.api.kg_content_routes import register_routes as register_kg_content_routes
from app.config.config_manager import ConfigManager
from app.database.manager import init_database


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 初始化数据库
    init_database(config_manager.get_database_config())
    
    # 创建FastAPI应用
    app = FastAPI(
        title="多类别知识图谱API",
        description="支持金融、科技、医疗、教育等多类别文本的知识图谱提取服务",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    # app.include_router(knowledge_graph_router)  # 该模块不存在
    
    # 注册知识图谱查询路由
    register_kg_query_routes(app)
    
    # 注册知识图谱内容处理路由
    register_kg_content_routes(app)
    
    # 配置静态文件服务 - 挂载前端文件
    frontend_path = Path(__file__).parent.parent / "frontend"
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
        
        # 添加根路径重定向到index.html
        @app.get("/")
        async def serve_index():
            from fastapi.responses import FileResponse
            index_file = frontend_path / "index.html"
            if index_file.exists():
                return FileResponse(str(index_file))
            return {
                "message": "多类别知识图谱API服务",
                "version": "2.0.0",
                "features": [
                    "多类别知识提取（金融、科技、医疗、教育）",
                    "类别兼容性检查",
                    "实体相似度比较",
                    "实体消歧与合并"
                ],
                "docs": "/docs"
            }
    
    # API根路径信息
    @app.get("/api")
    async def api_root():
        return {
            "message": "多类别知识图谱API服务",
            "version": "2.0.0",
            "features": [
                "多类别知识提取（金融、科技、医疗、教育）",
                "类别兼容性检查",
                "实体相似度比较",
                "实体消歧与合并"
            ],
            "docs": "/docs"
        }
    
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # 运行开发服务器
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8066,
        reload=True,
        log_level="info"
    )