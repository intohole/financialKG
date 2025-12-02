"""
知识图谱查询服务使用示例和FastAPI路由集成
展示如何将KGQueryService集成到FastAPI应用中
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from app.services.kg_query_service import KGQueryService
from app.database.manager import get_session
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

# 创建路由
router = APIRouter(prefix="/api/kg", tags=["知识图谱查询"])


# ==================== 依赖注入和工具函数 ====================

async def get_query_service() -> KGQueryService:
    """获取查询服务实例"""
    async for session in get_session():
        return KGQueryService(session)


async def handle_service_exception(operation: str, e: Exception) -> None:
    """统一处理服务层异常"""
    logger.error(f"{operation}失败: {e}", extra={
        "operation": operation,
        "error_type": type(e).__name__,
        "error_message": str(e)
    })
    
    if isinstance(e, HTTPException):
        raise e
    elif isinstance(e, ValueError):
        raise HTTPException(status_code=400, detail=f"{operation}参数错误: {str(e)}")
    else:
        raise HTTPException(status_code=500, detail=f"{operation}失败: {str(e)}")


# ==================== 实体相关API ====================

@router.get("/entities", summary="获取实体列表")
async def get_entities(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    query_service: KGQueryService = Depends(get_query_service)
):
    """
    获取实体列表，支持分页、搜索和过滤
    
    返回统一的分页格式：
    - items: 实体数据列表
    - total: 总数量
    - page: 当前页码
    - page_size: 每页数量
    - total_pages: 总页数
    """
    logger.info(f"获取实体列表: page={page}, page_size={page_size}, search={search}, entity_type={entity_type}")
    
    try:
        result = await query_service.get_entity_list(
            page=page,
            page_size=page_size,
            search=search,
            entity_type=entity_type,
            sort_by=sort_by,
            sort_order=sort_order
        )
        logger.info(f"成功获取实体列表: {result['total']}个实体")
        return result
    except Exception as e:
        await handle_service_exception("获取实体列表", e)


@router.get("/entities/{entity_id}", summary="获取实体详细信息")
async def get_entity_detail(
    entity_id: int,
    query_service: KGQueryService = Depends(get_query_service)
):
    """
    获取实体的详细信息，包含关联统计
    
    返回实体详细信息，包含：
    - 基本信息：名称、类型、描述等
    - 统计信息：关系数量、新闻数量、属性数量
    """
    logger.info(f"获取实体详情: entity_id={entity_id}")
    
    try:
        result = await query_service.get_entity_detail(entity_id)
        if not result:
            logger.warning(f"实体不存在: entity_id={entity_id}")
            raise HTTPException(status_code=404, detail="实体不存在")
        logger.info(f"成功获取实体详情: {result['name']}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        await handle_service_exception("获取实体详情", e)


# ==================== 关系相关API ====================

@router.get("/relations", summary="获取关系列表")
async def get_relations(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    entity_id: Optional[int] = Query(None, description="实体ID过滤"),
    relation_type: Optional[str] = Query(None, description="关系类型过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    query_service: KGQueryService = Depends(get_query_service)
):
    """
    获取关系列表，支持按实体和关系类型过滤
    
    返回关系数据，包含源实体和目标实体的详细信息
    """
    try:
        return await query_service.get_relation_list(
            page=page,
            page_size=page_size,
            entity_id=entity_id,
            relation_type=relation_type,
            search=search
        )
    except Exception as e:
        logger.error(f"获取关系列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取关系列表失败: {str(e)}")


# ==================== 网络分析API ====================

@router.get("/entities/{entity_id}/neighbors", summary="获取实体邻居网络")
async def get_entity_neighbors(
    entity_id: int,
    depth: int = Query(2, ge=1, le=5, description="遍历深度"),
    relation_types: Optional[List[str]] = Query(None, description="关系类型过滤"),
    max_entities: int = Query(100, ge=1, le=500, description="最大实体数量"),
    query_service: KGQueryService = Depends(get_query_service)
):
    """
    获取实体的邻居网络，适合图可视化展示
    
    返回图数据格式：
    - nodes: 实体节点列表
    - edges: 关系边列表
    - metadata: 网络统计信息
    """
    try:
        result = await query_service.get_entity_neighbors(
            entity_id=entity_id,
            depth=depth,
            relation_types=relation_types,
            max_entities=max_entities
        )
        
        if not result["nodes"]:
            raise HTTPException(status_code=404, detail="实体不存在或无关联数据")
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实体邻居网络失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实体邻居网络失败: {str(e)}")


# ==================== 实体-新闻关联API ====================

@router.get("/entities/{entity_id}/news", summary="获取实体关联的新闻")
async def get_entity_news(
    entity_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    query_service: KGQueryService = Depends(get_query_service)
):
    """
    获取实体关联的新闻，支持时间范围过滤
    
    返回分页的新闻数据，包含新闻的基本信息
    """
    try:
        return await query_service.get_entity_news(
            entity_id=entity_id,
            page=page,
            page_size=page_size,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"获取实体关联新闻失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实体关联新闻失败: {str(e)}")


@router.post("/entities/common-news", summary="获取多个实体的共同新闻")
async def get_common_news_for_entities(
    entity_ids: List[int] = Query(..., min_items=2, description="实体ID列表，至少2个"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    query_service: KGQueryService = Depends(get_query_service)
):
    """
    获取多个实体共同关联的新闻
    
    返回这些实体都关联的新闻，适合分析实体间的关联强度
    """
    try:
        return await query_service.get_common_news_for_entities(
            entity_ids=entity_ids,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"获取多实体共同新闻失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取多实体共同新闻失败: {str(e)}")


# ==================== 新闻列表查询API ====================

@router.get("/news", summary="获取新闻列表")
async def get_news_list(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（标题和内容）"),
    source: Optional[str] = Query(None, description="新闻来源过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    sort_by: str = Query("publish_time", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    query_service: KGQueryService = Depends(get_query_service)
):
    """
    获取新闻列表，支持分页、搜索和多维度过滤
    
    返回统一的分页格式：
    - items: 新闻数据列表
       - total: 总数量
    - page: 当前页码
    - page_size: 每页数量
    - total_pages: 总页数
    """
    logger.info(f"获取新闻列表: page={page}, page_size={page_size}, search={search}, source={source}")
    
    try:
        result = await query_service.get_news_list(
            page=page,
            page_size=page_size,
            search=search,
            source=source,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order
        )
        logger.info(f"成功获取新闻列表: {result['total']}条新闻")
        return result
    except Exception as e:
        await handle_service_exception("获取新闻列表", e)


@router.get("/news/search", summary="搜索新闻（向量搜索）")
async def search_news(
    query: str = Query(..., min_length=1, description="搜索查询词"),
    top_k: int = Query(20, ge=1, le=100, description="返回结果数量"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    query_service: KGQueryService = Depends(get_query_service)
):
    """
    使用向量搜索技术搜索新闻，支持语义搜索和时间范围过滤
    
    返回搜索结果列表，按相关性排序：
    - news_event: 新闻对象
    - score: 相关性分数
    - metadata: 搜索元数据
    """
    logger.info(f"搜索新闻: query='{query}', top_k={top_k}")
    
    try:
        # 使用KGQueryService的新闻搜索功能
        result = await query_service.news_search_service.search_news(
            query=query,
            top_k=top_k,
            start_date=start_date,
            end_date=end_date,
            enable_hybrid=True
        )
        
        # 转换结果为前端友好的格式
        formatted_results = []
        for item in result.get("results", []):
            news_event = item["news_event"]
            formatted_results.append({
                "news_event": {
                    "id": getattr(news_event, 'id', None),
                    "title": getattr(news_event, 'title', None),
                    "content": (getattr(news_event, 'content', '')[:300] + "..." if len(getattr(news_event, 'content', '')) > 300 else getattr(news_event, 'content', '')),
                    "source": getattr(news_event, 'source', None),
                    "published_at": getattr(news_event, 'publish_time', None).isoformat() if getattr(news_event, 'publish_time', None) else None,
                    "created_at": getattr(news_event, 'created_at', None).isoformat() if getattr(news_event, 'created_at', None) else None,
                    "updated_at": getattr(news_event, 'updated_at', None).isoformat() if getattr(news_event, 'updated_at', None) else None
                },
                "score": item["score"],
                "metadata": item["metadata"]
            })
        
        logger.info(f"搜索新闻完成: 找到{len(formatted_results)}个结果")
        return {
            "results": formatted_results,
            "query": query,
            "total": result.get("total", 0),
            "search_type": result.get("search_type", "database"),
            "fusion_weights": result.get("fusion_weights", {})
        }
        
    except Exception as e:
        await handle_service_exception("搜索新闻", e)


# ==================== 新闻-实体关联API ====================

@router.get("/news/{news_id}/entities", summary="获取新闻相关的实体")
async def get_news_entities(
    news_id: int,
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    limit: int = Query(50, ge=1, le=200, description="返回实体数量限制"),
    query_service: KGQueryService = Depends(get_query_service)
):
    """
    获取新闻相关的实体，按相关性排序
    
    返回相关实体列表，包含相关性评分
    """
    try:
        result = await query_service.get_news_entities(
            news_id=news_id,
            entity_type=entity_type,
            limit=limit
        )
        
        if not result["entities"]:
            raise HTTPException(status_code=404, detail="新闻不存在或无关联实体")
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取新闻相关实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取新闻相关实体失败: {str(e)}")


# ==================== 统计分析API ====================

@router.get("/statistics/overview", summary="获取知识图谱概览统计")
async def get_kg_statistics(
    query_service: KGQueryService = Depends(get_query_service)
):
    """
    获取知识图谱的概览统计信息
    
    返回：
    - 实体总数和类型分布
    - 关系总数和类型分布
    - 新闻总数
    - 实体-新闻关联总数
    """
    try:
        # 这里可以扩展实现更详细的统计功能
        # 暂时返回基础统计，后续可以在KGQueryService中添加专门的统计方法
        
        # 示例实现思路：
        # 1. 查询实体总数和按类型分组
        # 2. 查询关系总数和按类型分组
        # 3. 查询新闻总数
        # 4. 查询实体-新闻关联总数
        
        return {
            "message": "统计功能开发中",
            "available_endpoints": [
                "/api/kg/entities",
                "/api/kg/relations",
                "/api/kg/entities/{id}/neighbors",
                "/api/kg/entities/{id}/news",
                "/api/kg/entities/common-news",
                "/api/kg/news/{id}/entities"
            ]
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# ==================== 错误处理示例 ====================

@router.get("/test/error-handling", summary="测试错误处理")
async def test_error_handling():
    """测试错误处理机制"""
    try:
        # 模拟数据库错误
        raise Exception("数据库连接失败")
    except Exception as e:
        logger.error(f"测试错误处理: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# ==================== 路由注册示例 ====================

def register_routes(app):
    """
    注册知识图谱查询路由
    
    在main.py中使用：
    ```python
    from app.services import kg_query_routes
    
    # 注册路由
    kg_query_routes.register_routes(app)
    ```
    """
    app.include_router(router)