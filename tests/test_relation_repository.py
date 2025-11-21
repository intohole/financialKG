"""
RelationRepository 测试模块
测试关系存储库的所有功能
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from app.database.repositories import RelationRepository
from app.database.core import DatabaseError, NotFoundError


class TestRelationRepository:
    """RelationRepository 测试类"""
    
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
    def relation_repo(self, mock_session):
        """创建RelationRepository实例"""
        return RelationRepository(mock_session)
    
    @pytest.fixture
    def mock_relation(self):
        """创建模拟关系对象"""
        relation = MagicMock()
        relation.id = 1
        relation.subject_id = 1
        relation.predicate = "拥有"
        relation.object_id = 2
        return relation
    
    def create_mock_result(self, scalar_value=None, scalars_value=None, all_value=None):
        """创建模拟查询结果"""
        result = MagicMock()
        if scalar_value is not None:
            result.scalar_one_or_none = AsyncMock(return_value=scalar_value)
            result.scalar = AsyncMock(return_value=scalar_value)
        if scalars_value is not None:
            mock_scalars = MagicMock()
            mock_scalars.all = AsyncMock(return_value=scalars_value)
            result.scalars = MagicMock(return_value=mock_scalars)
        if all_value is not None:
            result.all = AsyncMock(return_value=all_value)
        return result
    
    async def mock_execute_result(self, scalars_value=None, all_value=None):
        """创建异步执行的模拟结果"""
        result = MagicMock()
        if scalars_value is not None:
            mock_scalars = MagicMock()
            mock_scalars.all = AsyncMock(return_value=scalars_value)
            result.scalars = MagicMock(return_value=mock_scalars)
        if all_value is not None:
            result.all = AsyncMock(return_value=all_value)
        return result
    
    @pytest.mark.asyncio
    async def test_init(self, mock_session):
        """测试初始化"""
        repo = RelationRepository(mock_session)
        assert repo.session == mock_session
    
    @pytest.mark.asyncio
    async def test_get_by_subject_success(self, relation_repo, mock_session, mock_relation):
        """测试根据主体获取关系 - 成功"""
        # 设置模拟结果
        relations = [mock_relation, mock_relation]
        mock_result = self.create_mock_result(scalars_value=relations)
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_subject(1, skip=0, limit=10)
        
        # 验证结果
        assert result == relations
        assert len(result) == 2
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert "subject_id" in str(call_args)
        assert "OFFSET" in str(call_args)
        assert "LIMIT" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_get_by_subject_empty(self, relation_repo, mock_session):
        """测试根据主体获取关系 - 空结果"""
        # 设置模拟结果
        mock_result = self.create_mock_result(scalars_value=[])
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_subject(999)
        
        # 验证结果
        assert result == []
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_by_object_success(self, relation_repo, mock_session, mock_relation):
        """测试根据客体获取关系 - 成功"""
        # 设置模拟结果
        relations = [mock_relation, mock_relation]
        mock_result = self.create_mock_result(scalars_value=relations)
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_object(2, skip=0, limit=10)
        
        # 验证结果
        assert result == relations
        assert len(result) == 2
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert "object_id" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_get_by_object_empty(self, relation_repo, mock_session):
        """测试根据客体获取关系 - 空结果"""
        # 设置模拟结果
        mock_result = self.create_mock_result(scalars_value=[])
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_object(999)
        
        # 验证结果
        assert result == []
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_by_predicate_success(self, relation_repo, mock_session, mock_relation):
        """测试根据谓词获取关系 - 成功"""
        # 设置模拟结果
        relations = [mock_relation, mock_relation]
        mock_result = self.create_mock_result(scalars_value=relations)
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_predicate("拥有", skip=0, limit=10)
        
        # 验证结果
        assert result == relations
        assert len(result) == 2
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert "predicate" in str(call_args)
        assert "拥有" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_get_by_predicate_empty(self, relation_repo, mock_session):
        """测试根据谓词获取关系 - 空结果"""
        # 设置模拟结果
        mock_result = self.create_mock_result(scalars_value=[])
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_predicate("不存在的谓词")
        
        # 验证结果
        assert result == []
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_triplets_with_all_params(self, relation_repo, mock_session, mock_relation):
        """测试获取三元组 - 使用所有参数"""
        # 设置模拟结果
        triplets = [mock_relation, mock_relation]
        mock_result = self.create_mock_result(scalars_value=triplets)
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_triplets(
            subject_id=1, 
            predicate="拥有", 
            object_id=2, 
            skip=0, 
            limit=10
        )
        
        # 验证结果
        assert result == triplets
        assert len(result) == 2
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert "subject_id" in str(call_args)
        assert "predicate" in str(call_args)
        assert "object_id" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_get_triplets_with_subject_only(self, relation_repo, mock_session):
        """测试获取三元组 - 仅指定主体"""
        # 设置模拟返回结果
        mock_relations = [
            self.create_mock_relation(id=1, subject_id=1, predicate="投资", object_id=2),
            self.create_mock_relation(id=2, subject_id=1, predicate="收购", object_id=3)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_triplets(subject_id=1)
        
        # 验证结果
        assert result == mock_relations
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_triplets_with_all_params(self, relation_repo, mock_session):
        """测试获取三元组 - 指定所有参数"""
        # 设置模拟返回结果
        mock_relations = [
            self.create_mock_relation(id=1, subject_id=1, predicate="投资", object_id=2)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_triplets(subject_id=1, predicate="投资", object_id=2)
        
        # 验证结果
        assert result == mock_relations
        assert len(result) == 1
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_triplets_with_predicate_only(self, relation_repo, mock_session):
        """测试获取三元组 - 仅使用谓词参数"""
        # 设置模拟返回结果
        mock_relations = [
            self.create_mock_relation(id=1, subject_id=1, predicate="拥有", object_id=2)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_triplets(predicate="拥有")
        
        # 验证结果
        assert result == mock_relations
        assert len(result) == 1
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_triplets_empty(self, relation_repo, mock_session):
        """测试获取三元组 - 空结果"""
        # 设置模拟结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_triplets(subject_id=999)
        
        # 验证结果
        assert result == []
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_update_entity_references_success(self, relation_repo, mock_session):
        """测试更新实体引用 - 成功"""
        # 设置模拟结果 - 更新影响的行数
        mock_result = MagicMock()
        mock_result.rowcount = 3  # 假设更新了3行
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.update_entity_references(1, 2)
        
        # 验证结果
        assert result is True
        assert mock_session.execute.call_count == 2  # 更新了subject和object两个字段
        
    @pytest.mark.asyncio
    async def test_update_entity_references_database_error(self, relation_repo, mock_session):
        """测试更新实体引用 - 数据库错误"""
        # 设置模拟结果 - 抛出异常
        mock_session.execute.side_effect = Exception("数据库错误")
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="数据库错误"):
            await relation_repo.update_entity_references(1, 2)
        
        # 验证执行被调用
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_relation_stats_success(self, relation_repo, mock_session):
        """测试获取关系统计 - 成功"""
        # 设置模拟返回结果
        mock_stats = [
            ("投资", 150),
            ("拥有", 80)
        ]
        mock_total = 230
        
        mock_result1 = MagicMock()
        mock_result1.all.return_value = mock_stats
        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = mock_total
        
        mock_session.execute.side_effect = [mock_result1, mock_result2]
        
        # 执行测试
        result = await relation_repo.get_relation_stats()
        
        # 验证结果
        assert result["total_relations"] == mock_total
        assert result["predicate_distribution"]["投资"] == 150
        assert result["predicate_distribution"]["拥有"] == 80
        assert mock_session.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_relation_stats_empty(self, relation_repo, mock_session):
        """测试获取关系统计 - 空结果"""
        # 设置模拟返回结果
        mock_stats = []
        mock_total = 0
        
        mock_result1 = MagicMock()
        mock_result1.all.return_value = mock_stats
        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = mock_total
        
        mock_session.execute.side_effect = [mock_result1, mock_result2]
        
        # 执行测试
        result = await relation_repo.get_relation_stats()
        
        # 验证结果
        assert result["total_relations"] == mock_total
        assert result["predicate_distribution"] == {}
        assert mock_session.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_relation_stats_database_error(self, relation_repo, mock_session):
        """测试获取关系统计 - 数据库错误"""
        # 设置异常
        mock_session.execute.side_effect = Exception("获取关系统计失败")
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="获取关系统计失败"):
            await relation_repo.get_relation_stats()
        
        # 验证执行被调用
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_redundant_relations_success(self, relation_repo, mock_session):
        """测试查找冗余关系 - 成功"""
        # 设置模拟返回结果
        mock_relations = [
            self.create_mock_relation(id=1, subject_id=1, predicate="投资", object_id=2),
            self.create_mock_relation(id=2, subject_id=1, predicate="投资", object_id=2)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.find_redundant_relations()
        
        # 验证结果
        assert result == mock_relations
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_redundant_relations_empty(self, relation_repo, mock_session):
        """测试查找冗余关系 - 空结果"""
        # 设置模拟返回结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.find_redundant_relations()
        
        # 验证结果
        assert result == []
        assert len(result) == 0
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_redundant_relations_database_error(self, relation_repo, mock_session):
        """测试查找冗余关系 - 数据库错误"""
        # 设置异常
        mock_session.execute.side_effect = Exception("查找冗余关系失败")
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="查找冗余关系失败"):
            await relation_repo.find_redundant_relations()
        
        # 验证执行被调用
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_subject_success(self, relation_repo, mock_session):
        """测试根据主体获取关系 - 成功"""
        # 设置模拟返回结果
        mock_relations = [
            self.create_mock_relation(id=1, subject_id=1, predicate="投资", object_id=2),
            self.create_mock_relation(id=2, subject_id=1, predicate="拥有", object_id=3)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_subject(1)
        
        # 验证结果
        assert result == mock_relations
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_subject_empty(self, relation_repo, mock_session):
        """测试根据主体获取关系 - 空结果"""
        # 设置模拟返回结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_subject(999)
        
        # 验证结果
        assert result == []
        assert len(result) == 0
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_object_success(self, relation_repo, mock_session):
        """测试根据客体获取关系 - 成功"""
        # 设置模拟返回结果
        mock_relations = [
            self.create_mock_relation(id=1, subject_id=1, predicate="投资", object_id=2),
            self.create_mock_relation(id=2, subject_id=3, predicate="拥有", object_id=2)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_object(2)
        
        # 验证结果
        assert result == mock_relations
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_object_empty(self, relation_repo, mock_session):
        """测试根据客体获取关系 - 空结果"""
        # 设置模拟返回结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_object(999)
        
        # 验证结果
        assert result == []
        assert len(result) == 0
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_predicate_success(self, relation_repo, mock_session):
        """测试根据谓词获取关系 - 成功"""
        # 设置模拟返回结果
        mock_relations = [
            self.create_mock_relation(id=1, subject_id=1, predicate="投资", object_id=2),
            self.create_mock_relation(id=2, subject_id=3, predicate="投资", object_id=4)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_relations
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_predicate("投资")
        
        # 验证结果
        assert result == mock_relations
        assert len(result) == 2
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_predicate_empty(self, relation_repo, mock_session):
        """测试根据谓词获取关系 - 空结果"""
        # 设置模拟返回结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await relation_repo.get_by_predicate("不存在的谓词")
        
        # 验证结果
        assert result == []
        assert len(result) == 0

    def create_mock_relation(self, id=1, subject_id=1, predicate="投资", object_id=2):
        """创建模拟关系对象"""
        relation = MagicMock()
        relation.id = id
        relation.subject_id = subject_id
        relation.predicate = predicate
        relation.object_id = object_id
        return relation