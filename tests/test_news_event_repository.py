"""
NewsEventRepository 测试模块
测试新闻事件存储库的所有功能
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.database.repositories import NewsEventRepository, DatabaseError
from app.database.core import DatabaseError, NotFoundError
from app.database.models import NewsEvent


class TestNewsEventRepository:
    """NewsEventRepository 测试类"""
    
    @pytest.fixture
    def mock_session(self):
        """创建模拟数据库会话"""
        session = MagicMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()
        return session
    
    @pytest.fixture
    def news_repo(self, mock_session):
        """创建NewsEventRepository实例"""
        return NewsEventRepository(mock_session)
    
    @pytest.fixture
    def mock_news_event(self):
        """创建模拟新闻事件对象"""
        news_event = MagicMock()
        news_event.id = 1
        news_event.title = "测试新闻标题"
        news_event.content = "测试新闻内容"
        news_event.source = "测试来源"
        news_event.publish_time = datetime.now()
        return news_event
    
    def create_mock_result(self, scalar_value=None, scalar_one_or_none_value=None, 
                          first_value=None, all_value=None):
        """创建模拟查询结果对象"""
        mock_result = MagicMock()
        
        # 设置 scalar 方法
        if scalar_value is not None:
            mock_result.scalar = MagicMock(return_value=scalar_value)
        else:
            mock_result.scalar = MagicMock(return_value=None)
        
        # 设置 scalar_one_or_none 方法
        if scalar_one_or_none_value is not None:
            mock_result.scalar_one_or_none = MagicMock(return_value=scalar_one_or_none_value)
        else:
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
        
        # 设置 first 方法
        if first_value is not None:
            mock_result.first = MagicMock(return_value=first_value)
        else:
            mock_result.first = MagicMock(return_value=None)
        
        # 设置 scalars 和 all 方法
        mock_scalars = MagicMock()
        if all_value is not None:
            mock_scalars.all = MagicMock(return_value=all_value)
        else:
            mock_scalars.all = MagicMock(return_value=[])
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        
        return mock_result
    
    @pytest.mark.asyncio
    async def test_init(self, mock_session):
        """测试初始化"""
        repo = NewsEventRepository(mock_session)
        assert repo.session == mock_session
    
    @pytest.mark.asyncio
    async def test_get_by_title_success_found(self, news_repo, mock_session, mock_news_event):
        """测试根据标题获取新闻事件 - 找到"""
        # 设置模拟结果
        mock_result = self.create_mock_result(scalar_one_or_none_value=mock_news_event)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.get_by_title("测试标题")
        
        # 验证结果
        assert result == mock_news_event
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_title_success_not_found(self, news_repo, mock_session):
        """测试根据标题获取新闻事件 - 未找到"""
        # 设置模拟结果
        mock_result = self.create_mock_result(scalar_one_or_none_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.get_by_title("不存在的标题")
        
        # 验证结果
        assert result is None
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_title_database_error(self, news_repo, mock_session):
        """测试根据标题获取新闻事件 - 数据库错误"""
        # 设置异常
        mock_session.execute.side_effect = SQLAlchemyError("数据库错误")
        
        # 执行测试并验证异常
        with pytest.raises(DatabaseError, match="根据标题获取新闻事件失败"):
            await news_repo.get_by_title("测试标题")
    
    @pytest.mark.asyncio
    async def test_get_by_source_success(self, news_repo, mock_session, mock_news_event):
        """测试根据来源获取新闻事件 - 成功"""
        # 设置模拟结果
        news_events = [mock_news_event, mock_news_event]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=news_events)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.get_by_source("测试来源")
        
        # 验证结果
        assert result == news_events
        assert len(result) == 2
        mock_session.execute.assert_called_once()
        # 验证SQL查询包含source条件
        call_args = mock_session.execute.call_args[0][0]
        assert "source" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_get_by_source_empty(self, news_repo, mock_session):
        """测试根据来源获取新闻事件 - 空结果"""
        # 设置模拟结果
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.get_by_source("不存在的来源")
        
        # 验证结果
        assert result == []
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_by_entity_success(self, news_repo, mock_session, mock_news_event):
        """测试根据实体获取相关新闻事件 - 成功"""
        # 设置模拟结果
        news_events = [mock_news_event, mock_news_event]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=news_events)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.get_by_entity(1, skip=0, limit=10)
        
        # 验证结果
        assert result == news_events
        assert len(result) == 2
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert "JOIN" in str(call_args)
        assert "entity_id" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_get_by_entity_empty(self, news_repo, mock_session):
        """测试根据实体获取相关新闻事件 - 空结果"""
        # 设置模拟结果
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.get_by_entity(999)
        
        # 验证结果
        assert result == []
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_add_entity_relation_success_new(self, news_repo, mock_session):
        """测试添加新闻事件与实体的关联 - 新关联"""
        # 设置模拟结果 - 关联不存在
        mock_result = self.create_mock_result(first_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.add_entity_relation(1, 1)
        
        # 验证结果 - 关联不存在时执行查询和插入两次调用
        assert result is True
        assert mock_session.execute.call_count == 2  # 查询 + 插入
    
    @pytest.mark.asyncio
    async def test_add_entity_relation_exists(self, news_repo, mock_session):
        """测试添加新闻事件与实体的关联 - 已存在"""
        # 设置模拟结果 - 关联已存在
        mock_result = self.create_mock_result(first_value=(1, 1))  # 返回一个存在的关联
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.add_entity_relation(1, 1)
        
        # 验证结果
        assert result is True
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_entity_relation_integrity_error(self, news_repo, mock_session):
        """测试添加新闻事件与实体的关联 - 完整性约束错误"""
        # 设置模拟结果 - 第一次查询正常，插入时抛出完整性错误
        mock_result = self.create_mock_result(first_value=None)
        mock_session.execute = AsyncMock(side_effect=[mock_result, IntegrityError("IntegrityError", None, None)])
        
        # 执行测试
        result = await news_repo.add_entity_relation(1, 1)
        
        # 验证结果 - 应该返回True（忽略完整性错误）
        assert result is True
        assert mock_session.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_add_entity_relation_database_error(self, news_repo, mock_session):
        """测试添加新闻事件与实体的关联 - 数据库错误"""
        # 设置异常
        mock_session.execute.side_effect = SQLAlchemyError("数据库错误")
        
        # 执行测试并验证异常
        with pytest.raises(DatabaseError, match="添加新闻事件与实体关联失败"):
            await news_repo.add_entity_relation(1, 1)
    
    @pytest.mark.asyncio
    async def test_remove_entity_relation_database_error(self, news_repo, mock_session):
        """测试移除新闻事件与实体的关联 - 数据库错误"""
        # 设置模拟异常
        mock_session.execute.side_effect = SQLAlchemyError("数据库错误")
        
        # 执行测试并验证异常
        with pytest.raises(DatabaseError, match="移除新闻事件与实体关联失败"):
            await news_repo.remove_entity_relation(1, 1)
    
    @pytest.mark.asyncio
    async def test_remove_entity_relation_success_exists(self, news_repo, mock_session):
        """测试移除新闻事件与实体的关联 - 关联存在"""
        # 设置模拟结果
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await news_repo.remove_entity_relation(1, 1)
        
        # 验证结果
        assert result is True
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert "DELETE" in str(call_args)
        assert "news_event_entity" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_remove_entity_relation_success_not_exists(self, news_repo, mock_session):
        """测试移除新闻事件与实体的关联 - 关联不存在"""
        # 设置模拟结果
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await news_repo.remove_entity_relation(1, 999)
        
        # 验证结果
        assert result is False
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_entity_relation_database_error(self, news_repo, mock_session):
        """测试移除新闻事件与实体的关联 - 数据库错误"""
        # 设置异常
        mock_session.execute.side_effect = SQLAlchemyError("数据库错误")
        
        # 执行测试并验证异常
        with pytest.raises(DatabaseError, match="移除新闻事件与实体关联失败"):
            await news_repo.remove_entity_relation(1, 1)
    
    @pytest.mark.asyncio
    async def test_get_recent_events_success(self, news_repo, mock_session, mock_news_event):
        """测试获取最近的新闻事件 - 成功"""
        # 设置模拟结果
        recent_events = [mock_news_event, mock_news_event]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=recent_events)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.get_recent_events(days=7, limit=10)
        
        # 验证结果
        assert result == recent_events
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recent_events_empty(self, news_repo, mock_session):
        """测试获取最近的新闻事件 - 空结果"""
        # 设置模拟结果
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.get_recent_events(days=7)
        
        # 验证结果
        assert result == []
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_by_content_success(self, news_repo, mock_session, mock_news_event):
        """测试根据内容关键词搜索新闻事件 - 成功"""
        # 设置模拟结果
        news_events = [mock_news_event, mock_news_event]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=news_events)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.search_by_content("关键词", limit=10)
        
        # 验证结果
        assert result == news_events
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_by_content_empty(self, news_repo, mock_session):
        """测试根据内容关键词搜索新闻事件 - 空结果"""
        # 设置模拟结果
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await news_repo.search_by_content("不存在的搜索词")
        
        # 验证结果
        assert result == []
        mock_session.execute.assert_called_once()