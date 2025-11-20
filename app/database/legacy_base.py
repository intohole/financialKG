"""
数据库基础抽象层
提供核心的数据库访问抽象和基础功能
"""

import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound
from sqlalchemy.pool import StaticPool

from sqlalchemy.orm import declarative_base
Base = declarative_base()

# 配置日志
logger = logging.getLogger(__name__)

# 类型定义
ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class DatabaseError(Exception):
    """数据库操作异常"""
    pass


class NotFoundError(DatabaseError):
    """数据不存在异常"""
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


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = create_async_engine(
            config.database_url,
            **config.get_engine_kwargs()
        )
        logger.info(f"数据库引擎创建成功: {config.database_url}")
    
    async def create_tables(self):
        """创建所有数据表"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("数据表创建成功")
        except SQLAlchemyError as e:
            logger.error(f"创建数据表失败: {e}")
            raise DatabaseError(f"创建数据表失败: {e}")
    
    async def drop_tables(self):
        """删除所有数据表"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("数据表删除成功")
        except SQLAlchemyError as e:
            logger.error(f"删除数据表失败: {e}")
            raise DatabaseError(f"删除数据表失败: {e}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """获取数据库会话"""
        session = AsyncSession(self.engine)
        try:
            yield session
        finally:
            await session.close()
    
    async def close(self):
        """关闭数据库连接"""
        await self.engine.dispose()
        logger.info("数据库连接已关闭")


class BaseRepository(Generic[ModelType]):
    """基础存储库类"""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
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


class UnitOfWork:
    """工作单元模式：管理多个存储库的事务"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
        self.session = None
        self.repositories = {}
    
    async def __aenter__(self):
        self.session = AsyncSession(self.database_manager.engine)
        # 延迟导入具体的存储库，避免循环依赖
        from .repositories import EntityRepository, RelationRepository, AttributeRepository, NewsEventRepository
        
        self.repositories = {
            'entities': EntityRepository(self.session),
            'relations': RelationRepository(self.session),
            'attributes': AttributeRepository(self.session),
            'news_events': NewsEventRepository(self.session)
        }
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self.session.commit()
                logger.info("工作单元事务提交成功")
            else:
                await self.session.rollback()
                logger.error(f"工作单元事务回滚: {exc_val}")
        finally:
            await self.session.close()
    
    def __getattr__(self, name):
        """动态获取存储库实例"""
        if name in self.repositories:
            return self.repositories[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    async def commit(self):
        """手动提交事务"""
        await self.session.commit()
    
    async def rollback(self):
        """手动回滚事务"""
        await self.session.rollback()


# 全局数据库管理器实例
_database_manager: Optional[DatabaseManager] = None


def init_database(config: DatabaseConfig) -> DatabaseManager:
    """初始化数据库"""
    global _database_manager
    _database_manager = DatabaseManager(config)
    return _database_manager


def get_database_manager() -> DatabaseManager:
    """获取数据库管理器"""
    if _database_manager is None:
        raise DatabaseError("数据库管理器未初始化")
    return _database_manager


async def get_session() -> AsyncIterator[AsyncSession]:
    """获取数据库会话（用于依赖注入）"""
    if _database_manager is None:
        raise DatabaseError("数据库管理器未初始化")
    async with _database_manager.get_session() as session:
        yield session