"""
数据库核心抽象层
提供数据库访问的核心抽象和基础组件
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select, insert, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.pool import StaticPool

from sqlalchemy.orm import declarative_base
Base = declarative_base()
from .manager import DatabaseManager

from app.utils.logging_utils import get_logger

# 配置日志
logger = get_logger(__name__)

# 类型定义
ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class DatabaseError(Exception):
    """数据库操作异常基类"""
    pass


class NotFoundError(DatabaseError):
    """数据未找到异常"""
    pass


class IntegrityError(DatabaseError):
    """数据完整性异常"""
    pass


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_pre_ping: bool = True,
        pool_recycle: int = 3600
    ):
        self.database_url = database_url or self._get_default_url()
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_pre_ping = pool_pre_ping
        self.pool_recycle = pool_recycle
    
    def _get_default_url(self) -> str:
        """获取默认数据库URL"""
        import os
        return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./knowledge_graph.db")
    
    def get_engine_kwargs(self) -> Dict[str, Any]:
        """获取引擎配置参数"""
        kwargs = {
            "echo": self.echo,
            "pool_pre_ping": self.pool_pre_ping,
            "pool_recycle": self.pool_recycle
        }
        
        # SQLite特殊配置
        if "sqlite" in self.database_url:
            kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False}
            })
        else:
            # PostgreSQL/MySQL连接池配置
            kwargs.update({
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow
            })
        
        return kwargs


class BaseRepository(Generic[ModelType]):
    """基础存储库抽象类"""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    @classmethod
    def create_with_manager(cls, database_manager: DatabaseManager):
        """使用数据库管理器创建存储库实例"""
        # 这是一个辅助方法，实际使用中会结合UnitOfWork模式
        pass
    
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """根据ID获取记录"""
        try:
            result = await self.session.get(self.model, id)
            return result
        except SQLAlchemyError as e:
            logger.error(f"获取记录失败: {e}")
            raise DatabaseError(f"获取记录失败: {e}")
    
    async def get_by_ids(self, ids: List[Any]) -> List[ModelType]:
        """根据多个ID获取记录"""
        try:
            stmt = select(self.model).where(self.model.id.in_(ids))
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"批量获取记录失败: {e}")
            raise DatabaseError(f"批量获取记录失败: {e}")
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        desc: bool = False
    ) -> List[ModelType]:
        """获取所有记录"""
        try:
            stmt = select(self.model)
            
            # 排序
            if order_by:
                order_field = getattr(self.model, order_by)
                if desc:
                    stmt = stmt.order_by(order_field.desc())
                else:
                    stmt = stmt.order_by(order_field)
            
            stmt = stmt.offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"获取所有记录失败: {e}")
            raise DatabaseError(f"获取所有记录失败: {e}")
    
    async def create(self, data: Dict[str, Any]) -> ModelType:
        """创建记录"""
        try:
            instance = self.model(**data)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            logger.info(f"创建记录成功: {self.model.__name__} - ID: {instance.id}")
            return instance
        except IntegrityError as e:
            logger.error(f"创建记录失败 - 完整性约束: {e}")
            raise IntegrityError(f"创建记录失败 - 数据完整性约束: {e}")
        except SQLAlchemyError as e:
            logger.error(f"创建记录失败: {e}")
            raise DatabaseError(f"创建记录失败: {e}")
    
    async def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """批量创建记录"""
        try:
            instances = [self.model(**data) for data in data_list]
            self.session.add_all(instances)
            await self.session.flush()
            
            # 刷新所有实例
            for instance in instances:
                await self.session.refresh(instance)
            
            logger.info(f"批量创建记录成功: {self.model.__name__} - 数量: {len(instances)}")
            return instances
        except IntegrityError as e:
            logger.error(f"批量创建记录失败 - 完整性约束: {e}")
            raise IntegrityError(f"批量创建记录失败 - 数据完整性约束: {e}")
        except SQLAlchemyError as e:
            logger.error(f"批量创建记录失败: {e}")
            raise DatabaseError(f"批量创建记录失败: {e}")
    
    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[ModelType]:
        """更新记录"""
        try:
            instance = await self.get_by_id(id)
            if not instance:
                raise NotFoundError(f"记录不存在: ID={id}")
            
            for key, value in data.items():
                setattr(instance, key, value)
            
            await self.session.flush()
            await self.session.refresh(instance)
            logger.info(f"更新记录成功: {self.model.__name__} - ID: {id}")
            return instance
        except NotFoundError:
            raise
        except IntegrityError as e:
            logger.error(f"更新记录失败 - 完整性约束: {e}")
            raise IntegrityError(f"更新记录失败 - 数据完整性约束: {e}")
        except SQLAlchemyError as e:
            logger.error(f"更新记录失败: {e}")
            raise DatabaseError(f"更新记录失败: {e}")
    
    async def delete(self, id: Any) -> bool:
        """删除记录"""
        try:
            instance = await self.get_by_id(id)
            if not instance:
                raise NotFoundError(f"记录不存在: ID={id}")
            
            await self.session.delete(instance)
            await self.session.flush()
            logger.info(f"删除记录成功: {self.model.__name__} - ID: {id}")
            return True
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"删除记录失败: {e}")
            raise DatabaseError(f"删除记录失败: {e}")
    
    async def bulk_delete(self, ids: List[Any]) -> int:
        """批量删除记录"""
        try:
            stmt = delete(self.model).where(self.model.id.in_(ids))
            result = await self.session.execute(stmt)
            deleted_count = result.rowcount
            logger.info(f"批量删除记录成功: {self.model.__name__} - 数量: {deleted_count}")
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"批量删除记录失败: {e}")
            raise DatabaseError(f"批量删除记录失败: {e}")
    
    async def count(self, **filters) -> int:
        """统计记录数量"""
        try:
            stmt = select(func.count(self.model.id))
            
            # 添加过滤条件
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        conditions.append(getattr(self.model, key) == value)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            result = await self.session.execute(stmt)
            return result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"统计记录数量失败: {e}")
            raise DatabaseError(f"统计记录数量失败: {e}")
    
    async def exists(self, **filters) -> bool:
        """检查记录是否存在"""
        try:
            count = await self.count(**filters)
            return count > 0
        except SQLAlchemyError as e:
            logger.error(f"检查记录存在性失败: {e}")
            raise DatabaseError(f"检查记录存在性失败: {e}")
    
    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """根据指定字段获取记录"""
        try:
            if not hasattr(self.model, field):
                raise ValueError(f"模型 {self.model.__name__} 不存在字段 {field}")
            
            stmt = select(self.model).where(getattr(self.model, field) == value)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"根据字段获取记录失败: {e}")
            raise DatabaseError(f"根据字段获取记录失败: {e}")
    
    async def get_by_fields(self, **filters) -> List[ModelType]:
        """根据多个字段获取记录"""
        try:
            stmt = select(self.model)
            conditions = []
            
            for key, value in filters.items():
                if hasattr(self.model, key):
                    conditions.append(getattr(self.model, key) == value)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"根据多个字段获取记录失败: {e}")
            raise DatabaseError(f"根据多个字段获取记录失败: {e}")