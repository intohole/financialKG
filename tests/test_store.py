"""
Store模块综合测试用例
测试HybridStore核心功能、向量索引管理、数据转换等
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor

from app.store.base import Entity, Relation, NewsEvent, StoreConfig
from app.store.hybrid_store import HybridStore
from app.store.hybrid_store_core import HybridStoreCore
from app.store.vector_index_manager import VectorIndexManager
from app.store.data_converter import DataConverter
from app.store.exceptions import StoreError, EntityNotFoundError, RelationNotFoundError, ValidationError
from app.vector.base import VectorSearchBase
from app.embedding import EmbeddingService


class TestDataConverter:
    """测试数据转换器"""
    
    def test_entity_conversion(self):
        """测试实体转换"""
        # 创建测试实体
        entity = Entity(
            id=1,
            name="测试实体",
            type="person",
            description="这是一个测试实体",
            metadata={"key": "value"}
        )
        
        # 转换为数据库实体
        db_entity = DataConverter.entity_to_db_entity(entity)
        
        # 验证转换结果
        assert db_entity["name"] == "测试实体"
        assert db_entity["type"] == "person"
        assert db_entity["description"] == "这是一个测试实体"
        assert db_entity["metadata"] == {"key": "value"}
        
        # 创建模拟数据库实体对象
        mock_db_entity = Mock()
        mock_db_entity.id = 1
        mock_db_entity.name = "测试实体"
        mock_db_entity.type = "person"
        mock_db_entity.description = "这是一个测试实体"
        mock_db_entity.canonical_id = None
        mock_db_entity.created_at = None
        mock_db_entity.updated_at = None
        mock_db_entity.metadata = {"key": "value"}
        
        # 转换回业务实体
        converted_entity = DataConverter.db_entity_to_entity(mock_db_entity, vector_id="vec_123")
        assert converted_entity.name == "测试实体"
        assert converted_entity.vector_id == "vec_123"
    
    def test_relation_conversion(self):
        """测试关系转换"""
        relation = Relation(
            id=1,
            subject_id=1,
            predicate="knows",
            object_id=2,
            description="测试关系",
            metadata={"confidence": 0.9}
        )
        
        db_relation = DataConverter.relation_to_db_relation(relation)
        assert db_relation["subject_id"] == 1
        assert db_relation["predicate"] == "knows"
        assert db_relation["object_id"] == 2
        
        # 创建模拟数据库关系对象
        mock_db_relation = Mock()
        mock_db_relation.id = 1
        mock_db_relation.subject_id = 1
        mock_db_relation.predicate = "knows"
        mock_db_relation.object_id = 2
        mock_db_relation.description = "测试关系"
        mock_db_relation.created_at = None
        mock_db_relation.metadata = {"confidence": 0.9}
        
        converted_relation = DataConverter.db_relation_to_relation(mock_db_relation, vector_id="vec_456")
        assert converted_relation.predicate == "knows"
        assert converted_relation.vector_id == "vec_456"
    
    def test_input_validation(self):
        """测试输入验证"""
        # 测试None输入
        with pytest.raises(ValueError):
            DataConverter.entity_to_db_entity(None)
        
        with pytest.raises(ValueError):
            DataConverter.db_entity_to_entity(None)
    
    def test_metadata_handling(self):
        """测试metadata字段处理"""
        # 测试缺少metadata的情况（metadata为None）
        mock_db_entity = Mock()
        mock_db_entity.id = 1
        mock_db_entity.name = "test"
        mock_db_entity.type = "person"
        mock_db_entity.description = None
        mock_db_entity.canonical_id = None
        mock_db_entity.created_at = None
        mock_db_entity.updated_at = None
        mock_db_entity.metadata = None
        
        entity = DataConverter.db_entity_to_entity(mock_db_entity)
        assert entity.metadata is None  # DataConverter保留None值
        
        # 测试有metadata的情况
        mock_db_entity_with_meta = Mock()
        mock_db_entity_with_meta.id = 1
        mock_db_entity_with_meta.name = "test"
        mock_db_entity_with_meta.type = "person"
        mock_db_entity_with_meta.description = None
        mock_db_entity_with_meta.canonical_id = None
        mock_db_entity_with_meta.created_at = None
        mock_db_entity_with_meta.updated_at = None
        mock_db_entity_with_meta.metadata = {"key": "value"}
        
        entity_with_meta = DataConverter.db_entity_to_entity(mock_db_entity_with_meta)
        assert entity_with_meta.metadata == {"key": "value"}


class TestVectorIndexManager:
    """测试向量索引管理器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.mock_vector_store = Mock()
        self.mock_embedding_service = Mock(spec=EmbeddingService)
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # 设置mock返回值 - VectorIndexManager使用的方法
        self.mock_embedding_service.embed_text.return_value = [0.1, 0.2, 0.3]
        self.mock_vector_store.add_vector.return_value = "vec_123"
        
        # 异步方法使用AsyncMock
        self.mock_vector_store.search_vectors_async = AsyncMock(return_value=[
            {"content_id": "1", "score": 0.9},
            {"content_id": "2", "score": 0.8}
        ])
        self.mock_vector_store.update_vector_async = AsyncMock(return_value=True)
        self.mock_vector_store.delete_vector_async = AsyncMock(return_value=True)
        self.mock_vector_store.health_check.return_value = "healthy"
        
        self.vector_manager = VectorIndexManager(
            self.mock_vector_store,
            self.mock_embedding_service,
            self.executor
        )
    
    @pytest.mark.asyncio
    async def test_add_to_index(self):
        """测试添加到向量索引"""
        vector_id = await self.vector_manager.add_to_index(
            content="测试内容",
            content_id="test_123",
            content_type="entity",
            metadata={"type": "person"}
        )
        
        assert vector_id == "vec_123"
        self.mock_embedding_service.embed_text.assert_called_once()
        self.mock_vector_store.add_vector.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_vectors(self):
        """测试向量搜索"""
        results = await self.vector_manager.search_vectors(
            query="测试查询",
            content_type="entity",
            limit=5
        )
        
        assert len(results) == 2
        assert results[0]["content_id"] == "1"
        assert results[0]["score"] == 0.9
    
    @pytest.mark.asyncio
    async def test_update_vector(self):
        """测试更新向量"""
        success = await self.vector_manager.update_vector(
            vector_id="vec_123",
            content="更新后的内容",
            metadata={"updated": True}
        )
        
        assert success is True
        self.mock_vector_store.update_vector_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_vector(self):
        """测试删除向量"""
        success = await self.vector_manager.delete_vector("vec_123")
        
        assert success is True
        self.mock_vector_store.delete_vector_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        health = await self.vector_manager.health_check()
        
        assert health["status"] == "healthy"
        assert health["vector_store"] == "healthy"
        assert health["embedding_service"] == "healthy"
    
    def teardown_method(self):
        """清理测试环境"""
        self.executor.shutdown(wait=True)


class TestHybridStoreCore:
    """测试HybridStore核心功能"""
    
    def setup_method(self):
        """设置测试环境"""
        self.mock_db_manager = AsyncMock()
        self.mock_vector_store = AsyncMock()
        self.mock_embedding_service = AsyncMock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # 设置mock数据库会话 - 正确设置异步上下文管理器
        self.mock_session = AsyncMock()
        self.mock_session.__aenter__ = AsyncMock(return_value=self.mock_session)
        self.mock_session.__aexit__ = AsyncMock(return_value=None)
        self.mock_db_manager.get_session = AsyncMock(return_value=self.mock_session)
        
        self.store = HybridStoreCore(
            self.mock_db_manager,
            self.mock_vector_store,
            self.mock_embedding_service,
            self.executor
        )
    
    @pytest.mark.asyncio
    async def test_create_entity(self):
        """测试创建实体"""
        # 设置mock返回值
        mock_entity_repo = AsyncMock()
        mock_entity_repo.create.return_value = Mock(
            id=1,
            name="测试实体",
            type="person",
            description="测试描述",
            metadata={}
        )
        
        # 设置Repository类 - 正确的mock方式
        with patch('app.store.hybrid_store_core.EntityRepository') as mock_entity_repo_class:
            mock_entity_repo_class.return_value = mock_entity_repo
            
            entity = Entity(
                id=None,  # 创建时ID为None，由数据库生成
                name="测试实体",
                type="person",
                description="测试描述"
            )
            
            # 这里需要模拟vector_manager的行为
            with patch.object(self.store.vector_manager, 'add_to_index', return_value="vec_123"):
                result = await self.store.create_entity(entity)
            
            assert result.name == "测试实体"
            assert result.type == "person"
        

    
    @pytest.mark.asyncio
    async def test_get_entity(self):
        """测试获取实体"""
        mock_entity_repo = AsyncMock()
        mock_entity_repo.get_by_id.return_value = Mock(
            id=1,
            name="测试实体",
            type="person",
            description="测试描述",
            metadata={}
        )
        
        self.mock_session.EntityRepository.return_value = mock_entity_repo
        
        result = await self.store.get_entity(1)
        
        assert result is not None
        assert result.name == "测试实体"
    
    @pytest.mark.asyncio
    async def test_entity_not_found(self):
        """测试实体未找到"""
        mock_entity_repo = AsyncMock()
        mock_entity_repo.get_by_id.return_value = None
        
        self.mock_session.EntityRepository.return_value = mock_entity_repo
        
        result = await self.store.get_entity(999)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_relation(self):
        """测试创建关系"""
        # 设置实体存在检查
        mock_entity_repo = AsyncMock()
        mock_entity_repo.get_by_id.side_effect = [
            Mock(id=1, name="主体"),
            Mock(id=2, name="客体")
        ]
        
        mock_relation_repo = AsyncMock()
        mock_relation_repo.create.return_value = Mock(
            id=1,
            subject_id=1,
            predicate="knows",
            object_id=2,
            description="测试关系"
        )
        
        self.mock_session.EntityRepository.return_value = mock_entity_repo
        self.mock_session.RelationRepository.return_value = mock_relation_repo
        
        relation = Relation(
            id=None,  # 创建时ID为None，由数据库生成
            subject_id=1,
            predicate="knows",
            object_id=2,
            description="测试关系"
        )
        
        with patch.object(self.store.vector_manager, 'add_to_index', return_value="vec_456"):
            result = await self.store.create_relation(relation)
        
        assert result.predicate == "knows"
        assert result.subject_id == 1
        assert result.object_id == 2
    
    @pytest.mark.asyncio
    async def test_search_entities(self):
        """测试实体搜索"""
        # 模拟向量搜索结果
        mock_search_results = [
            {"content_id": "1", "score": 0.9},
            {"content_id": "2", "score": 0.8}
        ]
        
        # 模拟实体获取
        mock_entity_repo = AsyncMock()
        mock_entity_repo.get_by_id.side_effect = [
            Mock(id=1, name="实体1", type="person", description="描述1", metadata={}),
            Mock(id=2, name="实体2", type="organization", description="描述2", metadata={})
        ]
        
        self.mock_session.EntityRepository.return_value = mock_entity_repo
        
        with patch.object(self.store.vector_manager, 'search_vectors', return_value=mock_search_results):
            results = await self.store.search_entities("测试查询", limit=2)
        
        assert len(results) == 2
        assert results[0].name == "实体1"
        assert results[1].name == "实体2"
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        self.mock_db_manager.health_check.return_value = {"status": "healthy"}
        
        with patch.object(self.store.vector_manager, 'health_check', return_value={"status": "healthy"}):
            health = await self.store.health_check()
        
        assert health["status"] == "healthy"
        assert "database" in health
        assert "vector_index" in health
    
    def teardown_method(self):
        """清理测试环境"""
        self.executor.shutdown(wait=True)


class TestExceptions:
    """测试异常处理"""
    
    def test_store_error(self):
        """测试基础存储异常"""
        error = StoreError("测试错误")
        assert str(error) == "测试错误"
    
    def test_entity_not_found_error(self):
        """测试实体未找到异常"""
        error = EntityNotFoundError(entity_id=123)
        assert "实体不存在" in str(error)
        assert error.entity_id == 123
    
    def test_relation_not_found_error(self):
        """测试关系未找到异常"""
        error = RelationNotFoundError(relation_id=456)
        assert "关系不存在" in str(error)
        assert error.relation_id == 456
    
    def test_validation_error(self):
        """测试验证异常"""
        error = ValidationError("验证失败", field="name")
        assert "验证失败" in str(error)
        assert error.field == "name"


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_entity_lifecycle(self):
        """测试实体完整生命周期"""
        # 创建实体
        entity = Entity(
            id=None,  # 集成测试中使用None作为ID
            name="集成测试实体",
            type="person",
            description="用于集成测试的实体"
        )
        
        # 这里应该使用真实的存储实例进行测试
        # 由于依赖较多，这里仅演示测试结构
        assert entity.name == "集成测试实体"
        assert entity.type == "person"
    
    @pytest.mark.asyncio
    async def test_relation_lifecycle(self):
        """测试关系完整生命周期"""
        relation = Relation(
            id=None,  # 集成测试中使用None作为ID
            subject_id=1,
            predicate="works_with",
            object_id=2,
            description="工作关系"
        )
        
        assert relation.predicate == "works_with"
        assert relation.subject_id == 1
        assert relation.object_id == 2


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])