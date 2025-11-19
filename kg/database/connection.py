"""
数据库连接管理模块

提供SQLite数据库的连接管理、会话创建和初始化功能
"""

import logging
import os
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.pool import StaticPool

# 导入新的配置系统
from kg.core.config_simple import config

from .models import Base

# 配置日志
logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器，负责数据库连接和会话管理"""

    def __init__(
        self, db_path: Optional[str] = None, config_path: Optional[str] = None
    ):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径，如果为None则从配置文件读取
            config_path: 配置文件路径，默认为项目根目录下的config.yaml
        """
        self.db_path = db_path
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml"
        )
        self.engine = None
        self.SessionLocal = None
        self._connection_lock = threading.Lock()
        self._initialize_database()

    def _load_config(self) -> dict:
        """加载配置文件（兼容旧版本）"""
        return {}

    def _get_db_path(self) -> str:
        """获取数据库文件路径"""
        if self.db_path:
            return self.db_path

        # 使用新的配置系统
        db_path = config.database.DB_PATH

        return os.path.abspath(db_path)

    def _initialize_database(self):
        """初始化数据库连接"""
        db_path = self._get_db_path()

        # 创建SQLite异步引擎
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            connect_args={
                "timeout": config.database.DB_TIMEOUT,  # 从配置获取超时时间
                "isolation_level": None,  # 自动提交模式
            },
            echo=config.database.DB_ECHO,  # 从配置获取回显设置
        )

        # 添加连接事件监听器，用于性能监控
        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            context._query_start_time = time.time()

        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            total = time.time() - context._query_start_time
            if total > 0.5:  # 记录执行时间超过0.5秒的查询
                logger.warning(f"慢查询: {statement[:100]}... 耗时: {total:.2f}秒")

        # 创建异步会话工厂
        self.SessionLocal = async_sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False, expire_on_commit=False
        )

        logger.info("数据库连接已初始化")

    async def create_tables_async(self):
        """异步创建数据库表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _create_tables(self):
        """异步创建数据库表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self):
        """获取数据库会话"""
        async with self.SessionLocal() as session:
            yield session

    @asynccontextmanager
    async def session_scope(self):
        """提供异步会话作用域的上下文管理器"""
        async with self.SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"数据库会话异常: {e}")
                raise
            finally:
                await session.close()

    async def check_connection(self) -> bool:
        """检查数据库连接是否正常"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            return False

    def reconnect(self):
        """重新连接数据库"""
        with self._connection_lock:
            try:
                self.close()
                self._initialize_database()
                logger.info("数据库重新连接成功")
            except Exception as e:
                logger.error(f"数据库重新连接失败: {e}")
                raise

    def close(self):
        """关闭数据库连接"""
        if self.SessionLocal:
            self.SessionLocal.remove()
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")


# 全局数据库管理器实例
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """获取全局数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_db_session():
    """获取数据库会话"""
    async for session in get_db_manager().get_session():
        yield session


@asynccontextmanager
async def db_session():
    """数据库会话上下文管理器"""
    async with get_db_manager().session_scope() as session:
        yield session


def init_database(
    db_path: Optional[str] = None, config_path: Optional[str] = None
) -> DatabaseManager:
    """
    初始化数据库

    Args:
        db_path: 数据库文件路径
        config_path: 配置文件路径

    Returns:
        DatabaseManager: 数据库管理器实例
    """
    global _db_manager
    _db_manager = DatabaseManager(db_path, config_path)
    return _db_manager


async def init_database_async(
    db_path: Optional[str] = None, config_path: Optional[str] = None
) -> DatabaseManager:
    """
    异步初始化数据库

    Args:
        db_path: 数据库文件路径
        config_path: 配置文件路径

    Returns:
        DatabaseManager: 数据库管理器实例
    """
    global _db_manager
    _db_manager = DatabaseManager(db_path, config_path)
    await _db_manager._create_tables()
    return _db_manager


def check_db_connection() -> bool:
    """检查数据库连接状态"""
    return get_db_manager().check_connection()


def reconnect_database():
    """重新连接数据库"""
    get_db_manager().reconnect()
