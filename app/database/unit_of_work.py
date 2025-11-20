"""
工作单元模式实现
提供事务管理和多存储库协调功能
"""

import logging
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from .core import DatabaseError
from .manager import DatabaseManager

# 配置日志
logger = logging.getLogger(__name__)


class UnitOfWork:
    """工作单元模式：管理多个存储库的事务"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
        self.session = None
        self.repositories = {}
    
    async def __aenter__(self):
        # 延迟导入避免循环导入
        from .core import DatabaseError
        from .repositories import EntityRepository, RelationRepository, AttributeRepository, NewsEventRepository
        
        self.session = AsyncSession(self.database_manager.engine)
        
        self.repositories = {
            'entities': EntityRepository(self.session),
            'relations': RelationRepository(self.session),
            'attributes': AttributeRepository(self.session),
            'news_events': NewsEventRepository(self.session)
        }
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 延迟导入避免循环导入
        from .core import DatabaseError
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