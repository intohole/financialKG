#!/usr/bin/env python3
"""
数据库迁移脚本
用于重新创建数据库表结构
"""

import asyncio
import logging
from app.config.config_manager import ConfigManager
from app.database.manager import init_database

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_database():
    """迁移数据库"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        
        # 获取数据库配置
        db_config = config_manager.get_database_config()
        
        # 初始化数据库管理器
        db_manager = init_database(db_config)
        
        logger.info("开始删除现有数据表...")
        await db_manager.drop_tables()
        logger.info("数据表删除完成")
        
        logger.info("开始创建新数据表...")
        await db_manager.create_tables()
        logger.info("数据表创建完成")
        
        # 关闭数据库连接
        await db_manager.close()
        logger.info("数据库迁移完成")
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate_database())