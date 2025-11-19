import pytest
from fastapi.testclient import TestClient
from kg.main import app
from kg.database.connection import DatabaseManager


@pytest.fixture(scope="module")
def test_client():
    """创建测试客户端"""
    yield TestClient(app)


@pytest.fixture(scope="module")
async def db_manager():
    """创建数据库管理器"""
    from kg.core.config_simple import config
    manager = DatabaseManager()
    yield manager
    # 清理资源
    await manager.close()
