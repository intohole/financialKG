"""
分页工具函数
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar("T")





async def get_paginated_data(
    db: AsyncSession,
    model,
    page: int = 1,
    page_size: int = 10,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    filters: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    获取分页数据的通用函数

    Args:
        db: 数据库会话
        model: SQLAlchemy模型类
        page: 页码
        page_size: 每页大小
        sort_by: 排序字段
        sort_order: 排序顺序 (asc/desc)
        filters: 过滤条件字典
        **kwargs: 额外的查询参数

    Returns:
        Dict: 包含分页数据的字典
    """
    # 构建查询
    query = select(model)

    # 应用过滤条件
    if filters:
        for key, value in filters.items():
            if value is not None:
                if hasattr(model, key):
                    column = getattr(model, key)
                    if isinstance(value, str):
                        # 对于字符串字段，支持模糊查询
                        query = query.where(column.ilike(f"%{value}%"))
                    else:
                        query = query.where(column == value)

    # 获取总记录数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # 计算分页信息
    if total == 0:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "pages": 0,
            "has_next": False,
            "has_prev": False,
        }

    pages = (total + page_size - 1) // page_size
    has_next = page < pages
    has_prev = page > 1

    # 应用排序
    if sort_by and hasattr(model, sort_by):
        column = getattr(model, sort_by)
        order_func = asc if sort_order.lower() == "asc" else desc
        query = query.order_by(order_func(column))

    # 应用分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # 执行查询
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "has_next": has_next,
        "has_prev": has_prev,
    }



