from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_database
from .api import include_routers

# 初始化数据库
init_database()

# 创建FastAPI应用
app = FastAPI(
    title="Knowledge Graph API",
    description="基于FastAPI的知识图谱API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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