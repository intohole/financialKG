"""
服务基类，提供通用的数据库操作和业务逻辑
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Dict, Generic, List, Optional, TypeVar
from sqlalchemy.orm import Session
import logging

from .pagination import get_paginated_data

ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    服务基类，提供CRUD操作的通用实现
    """
    
    def __init__(self, model: ModelType, logger: Optional[logging.Logger] = None):
        """
        初始化服务基类
        
        Args:
            model: SQLAlchemy模型类
            logger: 日志记录器实例
        """
        self.model = model
        self.logger = logger or logging.getLogger(__name__)
    
    async def create(
        self,
        db: AsyncSession,
        obj_in: CreateSchemaType
    ) -> Optional[ModelType]:
        """
        创建新对象
        
        Args:
            db: 数据库会话
            obj_in: 创建对象的数据
        
        Returns:
            创建的对象实例
        """
        try:
            # 如果obj_in是Pydantic模型，转换为字典
            if hasattr(obj_in, 'dict'):
                obj_in_data = obj_in.dict(exclude_unset=True)
            else:
                obj_in_data = obj_in
            
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            self.logger.error(f"创建{self.model.__name__}对象失败: {str(e)}")
            raise RuntimeError(f"创建{self.model.__name__}对象失败: {str(e)}")
    
    async def get(
        self,
        db: AsyncSession,
        obj_id: Any
    ) -> Optional[ModelType]:
        """
        通过ID获取对象
        
        Args:
            db: 数据库会话
            obj_id: 对象ID
        
        Returns:
            对象实例或None
        """
        try:
            query = select(self.model).where(self.model.id == obj_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(f"获取{self.model.__name__}对象失败: {str(e)}")
            raise RuntimeError(f"获取{self.model.__name__}对象失败: {str(e)}")
    
    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        获取多个对象
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            filters: 过滤条件字典
        
        Returns:
            对象列表
        """
        try:
            query = select(self.model)
            
            # 应用过滤条件
            if filters:
                for key, value in filters.items():
                    if value is not None and hasattr(self.model, key):
                        query = query.where(getattr(self.model, key) == value)
            
            # 应用分页
            query = query.offset(skip).limit(limit)
            
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error(f"获取{self.model.__name__}对象列表失败: {str(e)}")
            raise RuntimeError(f"获取{self.model.__name__}对象列表失败: {str(e)}")
    
    async def get_paginated(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取分页数据
        
        Args:
            db: 数据库会话
            page: 页码
            page_size: 每页大小
            sort_by: 排序字段
            sort_order: 排序顺序 (asc/desc)
            filters: 过滤条件字典
        
        Returns:
            包含分页信息的字典
        """
        return await get_paginated_data(
            db=db,
            model=self.model,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters
        )
    
    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelType,
        obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        """
        更新对象
        
        Args:
            db: 数据库会话
            db_obj: 数据库中的对象实例
            obj_in: 更新数据
        
        Returns:
            更新后的对象实例
        """
        try:
            # 如果obj_in是Pydantic模型，转换为字典
            if hasattr(obj_in, 'dict'):
                update_data = obj_in.dict(exclude_unset=True)
            else:
                update_data = obj_in
            
            # 更新对象属性
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            self.logger.error(f"更新{self.model.__name__}对象失败: {str(e)}")
            raise RuntimeError(f"更新{self.model.__name__}对象失败: {str(e)}")
    
    async def update_by_id(
        self,
        db: AsyncSession,
        obj_id: Any,
        obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        """
        通过ID更新对象
        
        Args:
            db: 数据库会话
            obj_id: 对象ID
            obj_in: 更新数据
        
        Returns:
            更新后的对象实例或None
        """
        db_obj = await self.get(db, obj_id)
        if not db_obj:
            return None
        return await self.update(db, db_obj, obj_in)
    
    async def delete(
        self,
        db: AsyncSession,
        obj_id: Any
    ) -> bool:
        """
        删除对象
        
        Args:
            db: 数据库会话
            obj_id: 对象ID
        
        Returns:
            是否删除成功
        """
        try:
            # 先检查对象是否存在
            db_obj = await self.get(db, obj_id)
            if not db_obj:
                return False
            
            # 执行删除
            query = delete(self.model).where(self.model.id == obj_id)
            result = await db.execute(query)
            await db.commit()
            
            # 检查是否有记录被删除
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            self.logger.error(f"删除{self.model.__name__}对象失败: {str(e)}")
            raise RuntimeError(f"删除{self.model.__name__}对象失败: {str(e)}")
    
    async def count(
        self,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        统计对象数量
        
        Args:
            db: 数据库会话
            filters: 过滤条件字典
        
        Returns:
            对象数量
        """
        try:
            from sqlalchemy import func
            query = select(func.count()).select_from(self.model)
            
            # 应用过滤条件
            if filters:
                for key, value in filters.items():
                    if value is not None and hasattr(self.model, key):
                        query = query.where(getattr(self.model, key) == value)
            
            result = await db.execute(query)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            self.logger.error(f"统计{self.model.__name__}对象数量失败: {str(e)}")
            raise RuntimeError(f"统计{self.model.__name__}对象数量失败: {str(e)}")
