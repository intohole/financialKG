"""FastAPI应用程序主文件

提供知识图谱的多类别支持API服务
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as knowledge_graph_router


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
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
    app.include_router(knowledge_graph_router)
    
    # 根路径
    @app.get("/")
    async def root():
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
        port=8000,
        reload=True,
        log_level="info"
    )