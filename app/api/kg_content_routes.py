"""
知识图谱内容处理路由

提供基于内容构建知识图谱的API端点
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.services.kg_core_impl import KGCoreImplService
from app.core.extract_models import KnowledgeGraph
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

# 创建路由
router = APIRouter(prefix="/api/kg", tags=["知识图谱内容处理"])


async def get_kg_core_service() -> KGCoreImplService:
    """
    获取KGCoreImplService实例
    
    注意：这里需要根据实际项目中的依赖注入方式调整
    """
    # 示例实现，实际项目中可能需要从配置或依赖注入容器中获取
    service = KGCoreImplService(auto_init_store=False)  # 关闭自动初始化，避免异步问题
    await service.initialize()  # 确保存储已初始化
    return service


from pydantic import BaseModel

class ProcessContentRequest(BaseModel):
    """处理内容请求模型"""
    content: str
    content_id: Optional[str] = None


@router.post("/process-content", summary="处理内容并构建知识图谱")
async def process_content(
    request: ProcessContentRequest,
    kg_core_service: KGCoreImplService = Depends(get_kg_core_service)
):
    """
    处理文本内容并构建知识图谱
    
    Args:
        content: 要处理的文本内容
        content_id: 内容ID（可选）
        
    Returns:
        KnowledgeGraph: 构建的知识图谱
    """
    try:
        logger.info(f"开始处理内容，长度: {len(request.content)}")
        
        # 调用核心服务处理内容
        knowledge_graph = await kg_core_service.process_content(request.content, request.content_id)
        
        logger.info("内容处理完成")
        return knowledge_graph
        
    except ValueError as e:
        logger.error(f"内容处理参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"处理内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理内容失败: {str(e)}")


def register_routes(app):
    """
    注册知识图谱内容处理路由
    
    在main.py中使用：
    ```python
    from app.api.kg_content_routes import register_routes
    
    # 注册路由
    register_routes(app)
    ```
    """
    app.include_router(router)