"""
数据库管理器模块
提供数据库连接管理和会话管理功能
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

# 避免循环导入，在函数内部导入
# from .core import DatabaseConfig, DatabaseError
from sqlalchemy.orm import declarative_base
Base = declarative_base()

# 配置日志
logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config):
        # 延迟导入避免循环导入
        from .core import DatabaseError
        self.config = config
        self._engine = None
        self._init_engine()
    
    def _init_engine(self):
        """初始化数据库引擎"""
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            
            self._engine = create_async_engine(
                self.config.database_url,
                **self.config.get_engine_kwargs()
            )
            logger.info(f"数据库引擎创建成功: {self.config.database_url}")
        except Exception as e:
            logger.error(f"数据库引擎初始化失败: {e}")
            raise DatabaseError(f"数据库引擎初始化失败: {e}")
    
    @property
    def engine(self):
        """获取数据库引擎"""
        from .core import DatabaseError
        if self._engine is None:
            raise DatabaseError("数据库引擎未初始化")
        return self._engine
    
    async def create_tables(self):
        """创建所有数据表"""
        from .core import DatabaseError
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("数据表创建成功")
        except SQLAlchemyError as e:
            logger.error(f"创建数据表失败: {e}")
            raise DatabaseError(f"创建数据表失败: {e}")
    
    async def drop_tables(self):
        """删除所有数据表"""
        from .core import DatabaseError
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
        if self._engine:
            await self._engine.dispose()
            logger.info("数据库连接已关闭")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            from sqlalchemy import text
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.scalar()
            return True
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False


# 全局数据库管理器实例
_database_manager = None


def init_database(config):
    """初始化数据库"""
    global _database_manager
    _database_manager = DatabaseManager(config)
    return _database_manager


def get_database_manager():
    """获取数据库管理器"""
    from .core import DatabaseError
    if _database_manager is None:
        raise DatabaseError("数据库管理器未初始化")
    return _database_manager


async def get_session():
    """获取数据库会话（用于依赖注入）"""
    from .core import DatabaseError
    if _database_manager is None:
        raise DatabaseError("数据库管理器未初始化")
    async with _database_manager.get_session() as session:
        yield session