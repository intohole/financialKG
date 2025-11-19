"""
路由基类和通用路由工具
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Generic, TypeVar, Optional, List
from pydantic import BaseModel

from ..utils.responses import SuccessResponse, ErrorResponse
from ..utils.exception_handlers import handle_value_error, handle_generic_exception
from .deps import get_db, get_logger

T = TypeVar('T')
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)
ResponseSchemaType = TypeVar('ResponseSchemaType', bound=BaseModel)


class BaseRouter:
    """
    API路由基类，提供通用的CRUD操作和响应处理
    """
    
    def __init__(self, prefix: str, tags: List[str], dependencies: Optional[List[Any]] = None):
        """
        初始化路由基类
        
        Args:
            prefix: 路由前缀
            tags: API标签
            dependencies: 路由依赖列表
        """
        self.router = APIRouter(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies or []
        )
        self.logger = get_logger()
    
    def get_router(self) -> APIRouter:
        """
        获取FastAPI路由实例
        
        Returns:
            APIRouter: FastAPI路由对象
        """
        return self.router
    
    async def handle_response(
        self,
        result: Any,
        message: str = "操作成功",
        success: bool = True,
        code: int = 200
    ) -> dict:
        """
        统一处理API响应
        
        Args:
            result: 响应数据
            message: 响应消息
            success: 是否成功
            code: 状态码
        
        Returns:
            dict: 格式化的响应数据
        """
        if success:
            return SuccessResponse(data=result, message=message).dict()
        else:
            return ErrorResponse(message=message, code=code).dict()
    
    async def handle_create(
        self,
        db: AsyncSession,
        create_data: CreateSchemaType,
        service_method,
        response_model: Optional[type] = None
    ) -> Any:
        """
        处理创建操作的通用方法
        
        Args:
            db: 数据库会话
            create_data: 创建数据
            service_method: 服务层创建方法
            response_model: 响应模型类
        
        Returns:
            Any: 创建结果
        """
        try:
            result = await service_method(db, create_data)
            # 如果提供了响应模型，进行转换
            if response_model and result:
                result = response_model.from_orm(result)
            return await self.handle_response(result, message="创建成功")
        except ValueError as e:
            raise handle_value_error(e, self.logger)
        except Exception as e:
            raise handle_generic_exception(e, self.logger, "创建")
    
    async def handle_get(
        self,
        db: AsyncSession,
        item_id: str,
        service_method,
        response_model: Optional[type] = None
    ) -> Any:
        """
        处理获取单个对象操作的通用方法
        
        Args:
            db: 数据库会话
            item_id: 对象ID
            service_method: 服务层获取方法
            response_model: 响应模型类
        
        Returns:
            Any: 获取结果
        """
        try:
            result = await service_method(db, item_id)
            if not result:
                raise HTTPException(status_code=404, detail="对象不存在")
            # 如果提供了响应模型，进行转换
            if response_model and result:
                result = response_model.from_orm(result)
            return await self.handle_response(result, message="获取成功")
        except HTTPException:
            raise
        except Exception as e:
            raise handle_generic_exception(e, self.logger, "获取")
    
    async def handle_list(
        self,
        db: AsyncSession,
        service_method,
        response_model: Optional[type] = None,
        **kwargs
    ) -> Any:
        """
        处理列表查询操作的通用方法
        
        Args:
            db: 数据库会话
            service_method: 服务层列表查询方法
            response_model: 响应模型类
            **kwargs: 额外的查询参数
        
        Returns:
            Any: 查询结果
        """
        try:
            # 记录查询参数
            self.logger.info(f"列表查询请求，参数: {kwargs}")
            
            # 准备调用参数
            call_kwargs = kwargs.copy()
            page = call_kwargs.pop('page', 1)
            limit = call_kwargs.pop('page_size', call_kwargs.pop('limit', 10))
            
            # 调用服务方法获取数据 - 简化参数传递逻辑
            if 'db' not in call_kwargs:
                # 默认添加db参数，除非已经存在
                call_kwargs['db'] = db
            
            items = await service_method(**call_kwargs)
            
            # 处理分页
            if page > 1 and limit > 0 and isinstance(items, list):
                start = (page - 1) * limit
                end = start + limit
                items = items[start:end]
            
            # 转换为响应模型
            if items:
                if isinstance(items, list) and response_model:
                    result = [response_model.from_orm(item) for item in items]
                elif response_model:
                    # 如果是单个对象，直接转换
                    result = response_model.from_orm(items)
                else:
                    result = items
            else:
                result = []
                
            self.logger.info(f"列表查询成功，返回 {len(result) if isinstance(result, list) else 1} 条数据")
            return await self.handle_response(result, message="查询成功")
        except Exception as e:
            self.logger.error(f"列表查询失败: {str(e)}")
            raise handle_generic_exception(e, self.logger, "查询")
    
    async def handle_update(
        self,
        db: AsyncSession,
        item_id: str,
        update_data: UpdateSchemaType,
        service_method,
        response_model: Optional[type] = None
    ) -> Any:
        """
        处理更新操作的通用方法
        
        Args:
            db: 数据库会话
            item_id: 对象ID
            update_data: 更新数据
            service_method: 服务层更新方法
            response_model: 响应模型类
        
        Returns:
            Any: 更新结果
        """
        try:
            result = await service_method(db, item_id, update_data)
            if not result:
                raise HTTPException(status_code=404, detail="对象不存在")
            # 如果提供了响应模型，进行转换
            if response_model and result:
                result = response_model.from_orm(result)
            return await self.handle_response(result, message="更新成功")
        except HTTPException:
            raise
        except ValueError as e:
            raise handle_value_error(e, self.logger)
        except Exception as e:
            raise handle_generic_exception(e, self.logger, "更新")
    
    async def handle_delete(
        self,
        db: AsyncSession,
        item_id: str,
        service_method
    ) -> Any:
        """
        处理删除操作的通用方法
        
        Args:
            db: 数据库会话
            item_id: 对象ID
            service_method: 服务层删除方法
        
        Returns:
            Any: 删除结果
        """
        try:
            result = await service_method(db, item_id)
            if not result:
                raise HTTPException(status_code=404, detail="对象不存在")
            return await self.handle_response(None, message="删除成功")
        except HTTPException:
            raise
        except Exception as e:
            raise handle_generic_exception(e, self.logger, "删除")
