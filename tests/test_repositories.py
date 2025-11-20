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
    async def test_create_success(self, entity_repo, mock_session):
        """测试创建实体 - 成功场景"""
        mock_entity = Mock()
        mock_entity.name = "测试实体"
        mock_entity.entity_type = "PERSON"
        mock_entity.description = "测试描述"
        
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await entity_repo.create(name="测试实体", entity_type="PERSON", description="测试描述")
        
        # 验证创建操作被调用
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_name_success(self, entity_repo, mock_session):
        """测试根据名称获取实体 - 成功场景"""
        mock_entity = Mock()
        mock_entity.name = "测试实体"
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.scalar_one_or_none.return_value = mock_entity
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.get_by_name("测试实体")
        
        assert result == mock_entity
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, entity_repo, mock_session):
        """测试根据名称获取实体 - 未找到场景"""
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.get_by_name("不存在的实体")
        
        assert result is None
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_type_success(self, entity_repo, mock_session):
        """测试根据类型获取实体 - 成功场景"""
        mock_entities = [Mock(), Mock()]
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_entities
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.get_by_type("PERSON")
        
        assert result == mock_entities
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_by_name_success(self, entity_repo, mock_session):
        """测试根据名称搜索实体 - 成功场景"""
        mock_entities = [Mock(), Mock(), Mock()]
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_entities
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.search_by_name("测试")
        
        assert result == mock_entities
        assert len(result) == 3
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_success(self, entity_repo, mock_session):
        """测试更新实体 - 成功场景"""
        mock_entity = Mock()
        mock_entity.name = "原名称"
        mock_entity.entity_type = "PERSON"
        mock_entity.description = "原描述"
        
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await entity_repo.update(mock_entity, name="新名称", description="新描述")
        
        assert result == mock_entity
        assert mock_entity.name == "新名称"
        assert mock_entity.description == "新描述"
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_success(self, entity_repo, mock_session):
        """测试删除实体 - 成功场景"""
        mock_entity = Mock()
        mock_entity.id = 1
        mock_entity.name = "测试实体"
        
        mock_session.flush = AsyncMock()
        
        await entity_repo.delete(mock_entity)
        
        mock_session.delete.assert_called_once_with(mock_entity)
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, entity_repo, mock_session):
        """测试根据ID获取实体 - 成功场景"""
        mock_entity = Mock()
        mock_entity.id = 1
        mock_entity.name = "测试实体"
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.scalar_one_or_none.return_value = mock_entity
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await entity_repo.get_by_id(1)
        
        assert result == mock_entity
        mock_session.execute.assert_called_once()


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
    async def test_create_success(self, relation_repo, mock_session):
        """测试创建关系 - 成功场景"""
        mock_relation = Mock()
        mock_relation.source_id = 1
        mock_relation.target_id = 2
        mock_relation.relation_type = "WORKS_FOR"
        
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await relation_repo.create(source_id=1, target_id=2, relation_type="WORKS_FOR")
        
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_entities_success(self, relation_repo, mock_session):
        """测试根据实体获取关系 - 成功场景"""
        mock_relations = [Mock(), Mock()]
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_relations
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.get_by_entities(1, 2)
        
        assert result == mock_relations
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_source_success(self, relation_repo, mock_session):
        """测试根据源实体获取关系 - 成功场景"""
        mock_relations = [Mock(), Mock(), Mock()]
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_relations
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.get_by_source(1)
        
        assert result == mock_relations
        assert len(result) == 3
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_target_success(self, relation_repo, mock_session):
        """测试根据目标实体获取关系 - 成功场景"""
        mock_relations = [Mock()]
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_relations
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.get_by_target(2)
        
        assert result == mock_relations
        assert len(result) == 1
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_type_success(self, relation_repo, mock_session):
        """测试根据关系类型获取关系 - 成功场景"""
        mock_relations = [Mock(), Mock(), Mock(), Mock()]
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_relations
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.get_by_type("WORKS_FOR")
        
        assert result == mock_relations
        assert len(result) == 4
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_by_entities_success(self, relation_repo, mock_session):
        """测试删除实体间关系 - 成功场景"""
        mock_result = AsyncMock()
        mock_result.rowcount = 2
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.delete_by_entities(1, 2)
        
        assert result == 2
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_by_entities_not_found(self, relation_repo, mock_session):
        """测试删除实体间关系 - 未找到场景"""
        mock_result = AsyncMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.delete_by_entities(1, 2)
        
        assert result == 0
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_find_redundant_relations_success(self, relation_repo, mock_session):
        """测试查找冗余关系 - 成功场景"""
        mock_relations = [Mock(), Mock()]
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_relations
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await relation_repo.find_redundant_relations(1, 2)
        
        assert result == mock_relations
        assert len(result) == 2
        mock_session.execute.assert_called_once()


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
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_attributes
        mock_result.scalars.return_value = mock_scalar_result
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
        mock_attribute.value = "25"
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.scalar_one_or_none.return_value = mock_attribute
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await attribute_repo.get_by_key(1, "age")
        
        assert result == mock_attribute
        assert result.key == "age"
        assert result.value == "25"
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_key_not_found(self, attribute_repo, mock_session):
        """测试根据键获取属性 - 未找到场景"""
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await attribute_repo.get_by_key(1, "不存在的键")
        
        assert result is None
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upsert_create_new(self, attribute_repo, mock_session):
        """测试upsert - 创建新属性场景"""
        # 模拟属性不存在
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await attribute_repo.upsert(1, "age", "25")
        
        # 验证创建操作被调用
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upsert_update_existing(self, attribute_repo, mock_session):
        """测试upsert - 更新现有属性场景"""
        mock_attribute = Mock()
        mock_attribute.key = "age"
        mock_attribute.value = "20"
        
        # 模拟属性存在
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.scalar_one_or_none.return_value = mock_attribute
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await attribute_repo.upsert(1, "age", "25")
        
        assert result == mock_attribute
        assert mock_attribute.value == "25"
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bulk_upsert_success(self, attribute_repo, mock_session):
        """测试批量upsert - 成功场景"""
        # 模拟属性不存在（创建新属性）
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        attributes = {"age": "25", "city": "北京", "job": "工程师"}
        result = await attribute_repo.bulk_upsert(1, attributes)
        
        assert len(result) == 3
        assert mock_session.add.call_count == 3
        assert mock_session.flush.call_count == 3
        assert mock_session.refresh.call_count == 3
    
    @pytest.mark.asyncio
    async def test_delete_by_entity_success(self, attribute_repo, mock_session):
        """测试删除实体属性 - 成功场景"""
        mock_attributes = [Mock(), Mock(), Mock()]
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_attributes
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await attribute_repo.delete_by_entity(1)
        
        assert result == 3
        assert mock_session.delete.call_count == 3
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
        mock_event = Mock()
        mock_event.title = "测试新闻"
        
        # 正确设置异步mock链 - 注意这里是scalar_one_or_none
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.scalar_one_or_none.return_value = mock_event
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.get_by_title("测试新闻")
        
        assert result == mock_event
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_source_success(self, news_event_repo, mock_session):
        """测试根据来源获取新闻事件 - 成功场景"""
        mock_events = [Mock()]
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_events
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.get_by_source("新浪新闻")
        
        assert result == mock_events
        assert len(result) == 1
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_entity_success(self, news_event_repo, mock_session):
        """测试根据实体获取新闻事件 - 成功场景"""
        mock_events = [Mock(), Mock(), Mock()]
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_events
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.get_by_entity(1)
        
        assert result == mock_events
        assert len(result) == 3
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_entity_relation_new_relation(self, news_event_repo, mock_session):
        """测试添加实体关联 - 新关联场景"""
        # 模拟查询结果 - 关联不存在
        mock_result = AsyncMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.add_entity_relation(1, 2)
        
        assert result is True
        assert mock_session.execute.call_count == 2  # 查询 + 插入
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_entity_relation_existing_relation(self, news_event_repo, mock_session):
        """测试添加实体关联 - 已存在关联场景"""
        # 模拟查询结果 - 关联已存在
        mock_result = AsyncMock()
        mock_result.first.return_value = Mock()  # 关联已存在
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.add_entity_relation(1, 2)
        
        assert result is True
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
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_events
        mock_result.scalars.return_value = mock_scalar_result
        mock_session.execute.return_value = mock_result
        
        result = await news_event_repo.get_recent_events(limit=5)
        
        assert result == mock_events
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_by_content_success(self, news_event_repo, mock_session):
        """测试根据内容搜索新闻事件 - 成功场景"""
        mock_events = [Mock(), Mock(), Mock()]
        
        # 正确设置异步mock链
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all.return_value = mock_events
        mock_result.scalars.return_value = mock_scalar_result
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