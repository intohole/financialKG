"""
数据库模块统一导出文件
提供简洁的数据库访问接口
"""

# 核心抽象层
from .core import (
    DatabaseError,
    NotFoundError,
    IntegrityError,
    DatabaseConfig,
    BaseRepository
)

# 数据库管理器
from .manager import (
    DatabaseManager,
    init_database,
    get_database_manager,
    get_session
)
from .repositories import EntityRepository, RelationRepository, AttributeRepository, NewsEventRepository


# 延迟导入具体存储库实现，避免循环导入问题
def __getattr__(name):
    if name in ['EntityRepository', 'RelationRepository', 'AttributeRepository', 'NewsEventRepository']:
        from .repositories import EntityRepository, RelationRepository, AttributeRepository, NewsEventRepository
        if name == 'EntityRepository':
            return EntityRepository
        elif name == 'RelationRepository':
            return RelationRepository
        elif name == 'AttributeRepository':
            return AttributeRepository
        elif name == 'NewsEventRepository':
            return NewsEventRepository
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    # 异常类
    'DatabaseError',
    'NotFoundError',
    'IntegrityError',
    
    # 配置类
    'DatabaseConfig',
    
    # 核心抽象
    'BaseRepository',
    'DatabaseManager',

    # 初始化函数
    'init_database',
    'get_database_manager',
    'get_session',
    
    # 具体存储库
    'EntityRepository',
    'RelationRepository',
    'AttributeRepository',
    'NewsEventRepository'
]