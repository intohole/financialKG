"""
测试配置和共享夹具
提供测试所需的通用配置和夹具
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database.core import DatabaseConfig, DatabaseManager
from app.database.manager import init_database, get_database_manager
from app.database.models import Base, Entity, Relation, Attribute, NewsEvent


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url():
    """测试数据库URL - 使用内存数据库"""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_database_config(test_database_url):
    """测试数据库配置"""
    return DatabaseConfig(
        database_url=test_database_url,
        echo=False,  # 测试时关闭SQL日志
        pool_size=1,
        max_overflow=0
    )


@pytest.fixture(scope="session")
async def database_manager(test_database_config):
    """数据库管理器夹具"""
    manager = init_database(test_database_config)
    
    # 创建所有表
    await manager.create_tables()
    
    yield manager
    
    # 清理
    await manager.drop_tables()
    await manager.close()


@pytest.fixture
def database_manager_fixture(database_manager):
    """数据库管理器夹具 - 函数级别"""
    return database_manager


@pytest.fixture
async def db_session(database_manager):
    """数据库会话夹具"""
    async with database_manager.get_session() as session:
        yield session
        # 回滚事务以保持测试隔离
        await session.rollback()


@pytest.fixture
def sample_entity_data():
    """示例实体数据"""
    return {
        "name": "Test Entity",
        "type": "PERSON",
        "description": "A test entity for unit tests"
    }


@pytest.fixture
def sample_relation_data():
    """示例关系数据"""
    return {
        "subject_id": 1,
        "predicate": "works_at",
        "object_id": 2,
        "description": "Test relationship"
    }


@pytest.fixture
def sample_attribute_data():
    """示例属性数据"""
    return {
        "entity_id": 1,
        "key": "age",
        "value": "30"
    }


@pytest.fixture
def sample_news_event_data():
    """示例新闻事件数据"""
    return {
        "title": "Test News Event",
        "content": "This is a test news event for unit testing",
        "source": "Test Source",
        "publish_time": datetime.utcnow()
    }


@pytest.fixture
def mock_datetime():
    """模拟日期时间"""
    return datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def cleanup_database(database_manager):
    """清理数据库夹具"""
    async def _cleanup():
        # 删除所有数据但保留表结构
        async with database_manager.get_session() as session:
            # 获取所有表名
            from sqlalchemy import inspect
            inspector = inspect(database_manager.engine)
            table_names = inspector.get_table_names()
            
            for table_name in table_names:
                await session.execute(f"DELETE FROM {table_name}")
            await session.commit()
    
    yield _cleanup


# 测试工具函数
def assert_entity_equal(entity1, entity2):
    """断言两个实体相等"""
    assert entity1.name == entity2.name
    assert entity1.type == entity2.type
    assert entity1.description == entity2.description


def assert_relation_equal(relation1, relation2):
    """断言两个关系相等"""
    assert relation1.subject_id == relation2.subject_id
    assert relation1.predicate == relation2.predicate
    assert relation1.object_id == relation2.object_id
    assert relation1.description == relation2.description


def assert_attribute_equal(attr1, attr2):
    """断言两个属性相等"""
    assert attr1.entity_id == attr2.entity_id
    assert attr1.key == attr2.key
    assert attr1.value == attr2.value


def assert_news_event_equal(event1, event2):
    """断言两个新闻事件相等"""
    assert event1.title == event2.title
    assert event1.content == event2.content
    assert event1.source == event2.source


# 异步测试辅助函数
async def create_test_entity(session, **kwargs):
    """创建测试实体"""
    from app.database.models import Entity
    
    entity_data = {
        "name": kwargs.get("name", "Test Entity"),
        "type": kwargs.get("type", "PERSON"),
        "description": kwargs.get("description", "Test description")
    }
    
    entity = Entity(**entity_data)
    session.add(entity)
    await session.flush()
    await session.refresh(entity)
    return entity


async def create_test_relation(session, subject_id, object_id, **kwargs):
    """创建测试关系"""
    from app.database.models import Relation
    
    relation_data = {
        "subject_id": subject_id,
        "object_id": object_id,
        "predicate": kwargs.get("predicate", "related_to"),
        "description": kwargs.get("description", "Test relation")
    }
    
    relation = Relation(**relation_data)
    session.add(relation)
    await session.flush()
    await session.refresh(relation)
    return relation


async def create_test_attribute(session, entity_id, **kwargs):
    """创建测试属性"""
    from app.database.models import Attribute
    
    attribute_data = {
        "entity_id": entity_id,
        "key": kwargs.get("key", "test_key"),
        "value": kwargs.get("value", "test_value")
    }
    
    attribute = Attribute(**attribute_data)
    session.add(attribute)
    await session.flush()
    await session.refresh(attribute)
    return attribute


async def create_test_news_event(session, **kwargs):
    """创建测试新闻事件"""
    from app.database.models import NewsEvent
    
    event_data = {
        "title": kwargs.get("title", "Test News"),
        "content": kwargs.get("content", "Test content"),
        "source": kwargs.get("source", "Test Source"),
        "publish_time": kwargs.get("publish_time", datetime.utcnow())
    }
    
    event = NewsEvent(**event_data)
    session.add(event)
    await session.flush()
    await session.refresh(event)
    return event