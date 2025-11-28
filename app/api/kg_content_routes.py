"""
知识图谱内容处理路由

提供基于内容构建知识图谱的API端点
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import asyncio
from contextlib import asynccontextmanager

from app.services.kg_core_impl import KGCoreImplService
from app.core.extract_models import KnowledgeGraph
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

# 创建路由
router = APIRouter(prefix="/api/kg", tags=["知识图谱内容处理"])


# 全局服务实例缓存，避免重复创建
_service_instance: Optional[KGCoreImplService] = None
_service_lock = asyncio.Lock()


@asynccontextmanager
async def get_kg_core_service() -> KGCoreImplService:
    """
    获取KGCoreImplService实例 - 使用单例模式和上下文管理
    
    优化点：
    1. 使用单例模式避免重复创建服务实例
    2. 使用异步锁确保线程安全
    3. 使用上下文管理器确保资源正确释放
    """
    global _service_instance
    
    async with _service_lock:
        if _service_instance is None:
            logger.info("初始化KGCoreImplService实例")
            _service_instance = KGCoreImplService(auto_init_store=False)
            await _service_instance.initialize()
        
        try:
            yield _service_instance
        except Exception as e:
            logger.error(f"服务使用异常: {e}")
            # 如果是严重错误，可以考虑重置服务实例
            if isinstance(e, RuntimeError):
                logger.warning("检测到运行时错误，重置服务实例")
                _service_instance = None
            raise


from pydantic import BaseModel

class ProcessContentRequest(BaseModel):
    """处理内容请求模型"""
    content: str
    content_id: Optional[str] = None
    
    def validate_content(self) -> None:
        """验证内容有效性"""
        if not self.content or not self.content.strip():
            raise ValueError("内容不能为空")
        
        content_length = len(self.content.strip())
        if content_length < 5:
            raise ValueError("内容太短，至少需要5个字符")
        if content_length > 10000:
            raise ValueError("内容太长，最多支持10000个字符")
        
        # 检查是否只有标点符号或空白字符
        import re
        if not re.search(r'[\u4e00-\u9fff\w]+', self.content):
            raise ValueError("内容必须包含有效的文本字符")


@router.post("/process-content", summary="处理内容并构建知识图谱")
async def process_content(
    request: ProcessContentRequest
):
    """
    处理文本内容并构建知识图谱
    
    Args:
        content: 要处理的文本内容
        content_id: 内容ID（可选）
        
    Returns:
        KnowledgeGraph: 构建的知识图谱
        
    Raises:
        HTTPException: 当参数无效或服务异常时
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        # 1. 参数验证
        request.validate_content()
        
        logger.info(f"开始处理内容，长度: {len(request.content)}, content_id: {request.content_id}")
        
        # 2. 使用上下文管理器获取服务实例
        async with get_kg_core_service() as kg_core_service:
            # 3. 调用核心服务处理内容
            knowledge_graph = await kg_core_service.process_content(
                request.content, 
                request.content_id
            )
            
            # 4. 性能监控
            processing_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"内容处理完成，耗时: {processing_time:.2f}s, "
                       f"实体: {len(knowledge_graph.entities)}, "
                       f"关系: {len(knowledge_graph.relations)}")
            
            # 5. 返回结果
            return knowledge_graph
        
    except ValueError as e:
        logger.warning(f"内容验证失败: {e}")
        raise HTTPException(status_code=400, detail=f"内容验证失败: {str(e)}")
    except asyncio.TimeoutError:
        logger.error(f"内容处理超时，耗时: {asyncio.get_event_loop().time() - start_time:.2f}s")
        raise HTTPException(status_code=504, detail="内容处理超时")
    except Exception as e:
        processing_time = asyncio.get_event_loop().time() - start_time
        logger.error(f"处理内容失败，耗时: {processing_time:.2f}s, 错误: {e}")
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