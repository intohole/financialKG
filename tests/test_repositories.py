"""
Repository测试套件
测试所有存储库的功能，确保符合大厂规范
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.database.repositories import (
    EntityRepository, RelationRepository, AttributeRepository, NewsEventRepository
)
from app.database.models import Entity, Relation, Attribute, NewsEvent, Base, news_event_entity
from app.database.core import DatabaseError, NotFoundError, IntegrityError as CoreIntegrityError


class TestEntityRepository:
    """实体存储库测试类"""
    
    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def entity_repo(self, mock_session):
        return EntityRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_init(self, mock_session):
        """测试实体存储库初始化"""
        repo = EntityRepository(mock_session)
        assert repo.session == mock_session
    
    @pytest.mark.asyncio
    async def test_get_by_name_success(self, entity_repo, mock_session):
        """测试根据名称获取实体 - 成功场景"""
        # 模拟查询结果
        mock_entity = Mock()
        mock_entity.id = 1
        mock_entity.name = "测试实体"
        mock_entity.type = "PERSON"
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_entity
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.get_by_name("测试实体")
        
        assert result == mock_entity
        assert result.name == "测试实体"
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, entity_repo, mock_session):
        """测试根据名称获取实体 - 未找到场景"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.get_by_name("不存在的实体")
        
        assert result is None
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_type_success(self, entity_repo, mock_session):
        """测试根据类型获取实体 - 成功场景"""
        mock_entities = [Mock(), Mock(), Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_entities
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.get_by_type("PERSON", skip=0, limit=10)
        
        assert result == mock_entities
        assert len(result) == 3
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_type_empty(self, entity_repo, mock_session):
        """测试根据类型获取实体 - 空结果场景"""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.get_by_type("ORGANIZATION")
        
        assert result == []
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_by_canonical_id_success(self, entity_repo, mock_session):
        """测试根据官方ID获取实体 - 成功场景"""
        mock_entities = [Mock(), Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_entities
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.get_by_canonical_id(1)
        
        assert result == mock_entities
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_merge_entities_success(self, entity_repo, mock_session):
        """测试合并实体 - 成功场景"""
        mock_canonical_entity = Mock()
        mock_canonical_entity.id = 1
        mock_alias_entity = Mock()
        mock_alias_entity.id = 2
        
        # 模拟get_by_id的返回值
        entity_repo.get_by_id = AsyncMock(side_effect=[mock_canonical_entity, mock_alias_entity])
        
        # 模拟查询结果
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.merge_entities(1, 2)
        
        assert result is True
        assert mock_alias_entity.canonical_id == 1
        assert mock_session.flush.called
    
    @pytest.mark.asyncio
    async def test_merge_entities_canonical_not_found(self, entity_repo, mock_session):
        """测试合并实体 - 官方实体不存在场景"""
        entity_repo.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="官方实体不存在"):
            await entity_repo.merge_entities(1, 2)
    
    @pytest.mark.asyncio
    async def test_merge_entities_alias_not_found(self, entity_repo, mock_session):
        """测试合并实体 - 别名实体不存在场景"""
        mock_canonical_entity = Mock()
        mock_canonical_entity.id = 1
        
        entity_repo.get_by_id = AsyncMock(side_effect=[mock_canonical_entity, None])
        
        with pytest.raises(ValueError, match="别名实体不存在"):
            await entity_repo.merge_entities(1, 2)
    
    @pytest.mark.asyncio
    async def test_search_entities_success(self, entity_repo, mock_session):
        """测试搜索实体 - 成功场景"""
        mock_entities = [Mock(), Mock(), Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_entities
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.search_entities("测试", limit=10)
        
        assert result == mock_entities
        assert len(result) == 3
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_entities_empty(self, entity_repo, mock_session):
        """测试搜索实体 - 空结果场景"""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.search_entities("不存在的实体")
        
        assert result == []
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_entity_relations_success(self, entity_repo, mock_session):
        """测试获取实体关系 - 成功场景"""
        mock_subject_relations = [Mock(), Mock()]
        mock_object_relations = [Mock()]
        
        # 模拟RelationRepository
        with patch('app.database.repositories.RelationRepository') as mock_relation_repo_class:
            mock_relation_repo = AsyncMock()
            mock_relation_repo_class.return_value = mock_relation_repo
            mock_relation_repo.get_by_subject.return_value = mock_subject_relations
            mock_relation_repo.get_by_object.return_value = mock_object_relations
            
            result = await entity_repo.get_entity_relations(1)
            
            assert len(result) == 3
            mock_relation_repo.get_by_subject.assert_called_once_with(1, 0, 100)
            mock_relation_repo.get_by_object.assert_called_once_with(1, 0, 100)
    
    @pytest.mark.asyncio
    async def test_get_entity_attributes_success(self, entity_repo, mock_session):
        """测试获取实体属性 - 成功场景"""
        mock_attributes = [Mock(), Mock()]
        
        with patch('app.database.repositories.AttributeRepository') as mock_attr_repo_class:
            mock_attr_repo = AsyncMock()
            mock_attr_repo_class.return_value = mock_attr_repo
            mock_attr_repo.get_by_entity.return_value = mock_attributes
            
            result = await entity_repo.get_entity_attributes(1)
            
            assert result == mock_attributes
            assert len(result) == 2
            mock_attr_repo.get_by_entity.assert_called_once_with(1)


class TestRelationRepository:
    """关系存储库测试类"""
    
    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def relation_repo(self, mock_session):
        return RelationRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_init(self, mock_session):
        """测试关系存储库初始化"""
        repo = RelationRepository(mock_session)
        assert repo.session == mock_session
    
    @pytest.mark.asyncio
    async def test_get_by_subject_success(self, relation_repo, mock_session):
        """测试根据主体获取关系 - 成功场景"""
        mock_relations = [Mock(), Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.get_by_subject(1, skip=0, limit=10)
        
        assert result == mock_relations
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_object_success(self, relation_repo, mock_session):
        """测试根据客体获取关系 - 成功场景"""
        mock_relations = [Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.get_by_object(2)
        
        assert result == mock_relations
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_by_predicate_success(self, relation_repo, mock_session):
        """测试根据谓词获取关系 - 成功场景"""
        mock_relations = [Mock(), Mock(), Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.get_by_predicate("works_at")
        
        assert result == mock_relations
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_get_triplets_with_all_params(self, relation_repo, mock_session):
        """测试获取三元组 - 全参数场景"""
        mock_relations = [Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.get_triplets(subject_id=1, predicate="works_at", object_id=2)
        
        assert result == mock_relations
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_triplets_no_params(self, relation_repo, mock_session):
        """测试获取三元组 - 无参数场景"""
        mock_relations = [Mock(), Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.get_triplets()
        
        assert result == mock_relations
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_update_entity_references_success(self, relation_repo, mock_session):
        """测试更新实体引用 - 成功场景"""
        mock_result1 = AsyncMock()
        mock_result2 = AsyncMock()
        mock_session.execute.side_effect = [mock_result1, mock_result2]
        
        result = await relation_repo.update_entity_references(1, 2)
        
        assert result is True
        assert mock_session.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_relation_stats_success(self, relation_repo, mock_session):
        """测试获取关系统计 - 成功场景"""
        mock_predicate_stats = [("works_at", 10), ("located_in", 5)]
        mock_total_count = 15
        
        # 模拟两个查询的返回值
        mock_result1 = AsyncMock()
        mock_result1.all.return_value = mock_predicate_stats
        
        mock_result2 = AsyncMock()
        mock_result2.scalar.return_value = mock_total_count
        
        mock_session.execute.side_effect = [mock_result1, mock_result2]
        
        result = await relation_repo.get_relation_stats()
        
        assert result["total_relations"] == 15
        assert result["predicate_distribution"]["works_at"] == 10
        assert result["predicate_distribution"]["located_in"] == 5
        assert mock_session.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_find_redundant_relations_success(self, relation_repo, mock_session):
        """测试查找冗余关系 - 成功场景"""
        mock_relations = [Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.find_redundant_relations()
        
        assert result == mock_relations
        assert len(result) == 1


class TestAttributeRepository:
    """属性存储库测试类"""
    
    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def attribute_repo(self, mock_session):
        return AttributeRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_init(self, mock_session):
        """测试属性存储库初始化"""
        repo = AttributeRepository(mock_session)
        assert repo.session == mock_session
    
    @pytest.mark.asyncio
    async def test_get_by_entity_success(self, attribute_repo, mock_session):
        """测试根据实体获取属性 - 成功场景"""
        mock_attributes = [Mock(), Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_attributes
        mock_session.execute.return_value = mock_result
        
        result = await attribute_repo.get_by_entity(1)
        
        assert result == mock_attributes
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_key_success(self, attribute_repo, mock_session):
        """测试根据键获取属性 - 成功场景"""
        mock_attribute = Mock()
        mock_attribute.key = "age"
        mock_attribute.value = "30"
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_attribute
        mock_session.execute.return_value = mock_result
        
        result = await attribute_repo.get_by_key(1, "age")
        
        assert result == mock_attribute
        assert result.key == "age"
        assert result.value == "30"
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_key_not_found(self, attribute_repo, mock_session):
        """测试根据键获取属性 - 未找到场景"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await attribute_repo.get_by_key(1, "nonexistent")
        
        assert result is None
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_by_entity_success(self, attribute_repo, mock_session):
        """测试删除实体属性 - 成功场景"""
        mock_result = AsyncMock()
        mock_result.rowcount = 3
        mock_session.execute.return_value = mock_result
        
        result = await attribute_repo.delete_by_entity(1)
        
        assert result == 3
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()


class TestNewsEventRepository:
    """新闻事件存储库测试类"""
    
    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def news_event_repo(self, mock_session):
        return NewsEventRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_init(self, mock_session):
        """测试新闻事件存储库初始化"""
        repo = NewsEventRepository(mock_session)
        assert repo.session == mock_session
    
    @pytest.mark.asyncio
    async def test_get_by_title_success(self, news_event_repo, mock_session):
        """测试根据标题获取新闻事件 - 成功场景"""
        mock_events = [Mock(), Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.get_by_title("测试新闻")
        
        assert result == mock_events
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_source_success(self, news_event_repo, mock_session):
        """测试根据来源获取新闻事件 - 成功场景"""
        mock_events = [Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.get_by_source("新浪新闻")
        
        assert result == mock_events
        assert len(result) == 1
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_entity_success(self, news_event_repo, mock_session):
        """测试根据实体获取新闻事件 - 成功场景"""
        mock_events = [Mock(), Mock(), Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.get_by_entity(1)
        
        assert result == mock_events
        assert len(result) == 3
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_entity_relation_new_relation(self, news_event_repo, mock_session):
        """测试添加实体关联 - 新关联场景"""
        mock_event = Mock()
        mock_event.id = 1
        mock_entity = Mock()
        mock_entity.id = 2
        
        # 模拟查询结果 - 关联不存在
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.add_entity_relation(1, 2)
        
        assert result is True
        assert mock_session.execute.call_count == 2  # 查询 + 插入
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_entity_relation_existing_relation(self, news_event_repo, mock_session):
        """测试添加实体关联 - 已存在关联场景"""
        mock_event = Mock()
        mock_event.id = 1
        mock_entity = Mock()
        mock_entity.id = 2
        
        # 模拟查询结果 - 关联已存在
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = Mock()  # 关联已存在
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.add_entity_relation(1, 2)
        
        assert result is False
        mock_session.execute.assert_called_once()  # 只有查询，没有插入
        mock_session.flush.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_entity_relation_success(self, news_event_repo, mock_session):
        """测试移除实体关联 - 成功场景"""
        # 模拟删除结果
        mock_result = AsyncMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.remove_entity_relation(1, 2)
        
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_entity_relation_not_found(self, news_event_repo, mock_session):
        """测试移除实体关联 - 未找到关联场景"""
        # 模拟删除结果
        mock_result = AsyncMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.remove_entity_relation(1, 2)
        
        assert result is False
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_recent_events_success(self, news_event_repo, mock_session):
        """测试获取最近新闻事件 - 成功场景"""
        mock_events = [Mock(), Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.get_recent_events(limit=5)
        
        assert result == mock_events
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_by_content_success(self, news_event_repo, mock_session):
        """测试根据内容搜索新闻事件 - 成功场景"""
        mock_events = [Mock(), Mock(), Mock()]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.search_by_content("关键词")
        
        assert result == mock_events
        assert len(result) == 3
        mock_session.execute.assert_called_once()


class TestIntegration:
    """集成测试类"""
    
    @pytest.mark.asyncio
    async def test_entity_lifecycle(self):
        """测试实体生命周期 - 从创建到删除的完整流程"""
        # 这个测试需要真实的数据库连接
        # 在实际项目中应该使用测试数据库
        pass
    
    @pytest.mark.asyncio
    async def test_relation_lifecycle(self):
        """测试关系生命周期 - 从创建到删除的完整流程"""
        pass
    
    @pytest.mark.asyncio
    async def test_attribute_management(self):
        """测试属性管理 - 动态属性操作"""
        pass
    
    @pytest.mark.asyncio
    async def test_news_event_entity_association(self):
        """测试新闻事件与实体关联 - 多对多关系管理"""
        pass


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])