"""
API路由初始化模块

此模块负责组织和注册系统的所有API路由。它创建主路由并包含各个功能模块的
子路由，然后提供一个统一的函数将所有路由注册到FastAPI应用中。

系统API组织如下：
- entities_router: 实体管理相关API
- relations_router: 关系管理相关API
- news_router: 新闻处理相关API
- deduplication_router: 实体关系去重相关API
"""

from fastapi import APIRouter

# 创建主路由
router = APIRouter()

# 导入所有子路由
from .entities_router import entities_router
from .relations_router import relations_router
from .news_router import news_router
from .deduplication_router import deduplication_router

# 将子路由包含到主路由中
router.include_router(entities_router)
router.include_router(relations_router)
router.include_router(news_router)
router.include_router(deduplication_router)

def include_routers(app):
    """
    将所有路由注册到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    app.include_router(router, prefix="/api/v1")
