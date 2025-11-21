"""
AttributeRepository 测试模块
测试属性存储库的所有功能
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.exc import SQLAlchemyError
from app.database.repositories import AttributeRepository
from app.database.core import DatabaseError


class TestAttributeRepository:
    """AttributeRepository 测试类"""
    
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
    def attribute_repo(self, mock_session):
        """创建AttributeRepository实例"""
        return AttributeRepository(mock_session)
    
    @pytest.fixture
    def mock_attribute(self):
        """创建模拟属性对象"""
        attribute = MagicMock()
        attribute.id = 1
        attribute.entity_id = 1
        attribute.key = "行业"
        attribute.value = "科技"
        return attribute
    
    def create_mock_result(self, scalar_value=None, scalars_value=None, all_value=None):
        """创建模拟查询结果"""
        result = MagicMock()
        if scalar_value is not None:
            result.scalar_one_or_none = AsyncMock(return_value=scalar_value)
            result.scalar = AsyncMock(return_value=scalar_value)
        if scalars_value is not None:
            mock_scalars = MagicMock()
            mock_scalars.all = AsyncMock(return_value=scalars_value)
            result.scalars.return_value = mock_scalars
        if all_value is not None:
            result.all = AsyncMock(return_value=all_value)
        
        return result
    
    def create_awaitable_mock_result(self, scalars_value=None, scalar_value=None):
        """创建可等待的模拟结果"""
        # 创建模拟结果对象
        mock_result = MagicMock()
        if scalars_value is not None:
            # 创建scalars对象，模拟all()方法
            mock_scalars = MagicMock()
            mock_scalars.all.return_value = scalars_value
            mock_result.scalars.return_value = mock_scalars
        if scalar_value is not None:
            # 直接设置scalar_one_or_none的值
            mock_result.scalar_one_or_none.return_value = scalar_value
        elif scalar_value is None:
            # 显式设置为None
            mock_result.scalar_one_or_none.return_value = None
        return mock_result
    
    def create_mock_result(self, scalars_value=None, scalar_value=None):
        """创建普通模拟结果（非异步）"""
        mock_result = MagicMock()
        if scalars_value is not None:
            mock_scalars = MagicMock()
            mock_scalars.all.return_value = scalars_value
            mock_result.scalars.return_value = mock_scalars
        if scalar_value is not None:
            mock_result.scalar_one_or_none.return_value = scalar_value
        elif scalar_value is None:
            mock_result.scalar_one_or_none.return_value = None
        return mock_result
    
    @pytest.mark.asyncio
    async def test_init(self, mock_session):
        """测试初始化"""
        repo = AttributeRepository(mock_session)
        assert repo.session == mock_session
    
    @pytest.mark.asyncio
    async def test_get_by_entity_success(self, attribute_repo, mock_session, mock_attribute):
        """测试根据实体获取属性 - 成功"""
        # 设置模拟结果
        attributes = [mock_attribute, mock_attribute]
        mock_result = self.create_awaitable_mock_result(scalars_value=attributes)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await attribute_repo.get_by_entity(1)
        
        # 验证结果
        assert result == attributes
        assert len(result) == 2
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert "entity_id" in str(call_args)
        assert str(1) in str(call_args)
    
    @pytest.mark.asyncio
    async def test_get_by_entity_empty(self, attribute_repo, mock_session):
        """测试根据实体获取属性 - 空结果"""
        # 设置模拟结果
        mock_result = self.create_awaitable_mock_result(scalars_value=[])
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await attribute_repo.get_by_entity(999)
        
        # 验证结果
        assert result == []
        assert len(result) == 0
        mock_session.execute.assert_called_once()
        
        # 执行测试
        result = await attribute_repo.get_by_entity(999)
        
        # 验证结果
        assert result == []
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_by_entity_database_error(self, attribute_repo, mock_session):
        """测试根据实体获取属性 - 数据库错误"""
        # 设置异常
        mock_session.execute.side_effect = SQLAlchemyError("数据库错误")
        
        # 执行测试并验证异常
        with pytest.raises(DatabaseError, match="根据实体获取属性失败"):
            await attribute_repo.get_by_entity(1)
    
    @pytest.mark.asyncio
    async def test_get_by_key_success_found(self, attribute_repo, mock_session, mock_attribute):
        """测试根据键获取属性 - 找到"""
        # 设置模拟结果
        mock_result = self.create_awaitable_mock_result(scalar_value=mock_attribute)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await attribute_repo.get_by_key(1, "行业")
        
        # 验证结果
        assert result is mock_attribute
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_key_success_not_found(self, attribute_repo, mock_session):
        """测试根据键获取属性 - 未找到"""
        # 设置模拟结果
        mock_result = self.create_awaitable_mock_result(scalar_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await attribute_repo.get_by_key(1, "不存在的键")
        
        # 验证结果
        assert result is None
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_key_database_error(self, attribute_repo, mock_session):
        """测试根据键获取属性 - 数据库错误"""
        # 设置异常
        mock_session.execute.side_effect = SQLAlchemyError("数据库错误")
        
        # 执行测试并验证异常
        with pytest.raises(DatabaseError, match="根据键获取属性失败"):
            await attribute_repo.get_by_key(1, "测试键")
    
    @pytest.mark.asyncio
    async def test_upsert_update_existing(self, attribute_repo, mock_session, mock_attribute):
        """测试upsert - 更新现有属性"""
        # 设置模拟结果 - 属性已存在
        mock_result = self.create_mock_result(scalar_value=mock_attribute)
        mock_session.execute.return_value = mock_result
        
        # 执行测试
        result = await attribute_repo.upsert(1, "行业", "金融")
        
        # 验证结果
        assert result is mock_attribute
        mock_attribute.value = "金融"  # 验证值已更新
        mock_session.execute.assert_called_once()  # 只执行了查询
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_attribute)
    
    @pytest.mark.asyncio
    async def test_upsert_database_error_on_update(self, attribute_repo, mock_session, mock_attribute):
        """测试upsert - 更新时数据库错误"""
        # 设置模拟结果 - 属性已存在
        mock_result = self.create_mock_result(scalar_value=mock_attribute)
        mock_session.execute.return_value = mock_result
        
        # 设置flush异常
        mock_session.flush.side_effect = SQLAlchemyError("数据库错误")
        
        # 执行测试并验证异常
        with pytest.raises(DatabaseError, match="属性upsert失败"):
            await attribute_repo.upsert(1, "行业", "金融")
    
    @pytest.mark.asyncio
    async def test_upsert_database_error_on_create(self, attribute_repo, mock_session):
        """测试upsert - 创建时数据库错误"""
        # 设置模拟结果 - 属性不存在
        mock_result = self.create_mock_result(scalar_value=None)
        mock_session.execute.return_value = mock_result
        
        # 模拟create方法抛出异常
        with patch.object(attribute_repo, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = SQLAlchemyError("数据库错误")
            
            # 执行测试并验证异常
            with pytest.raises(DatabaseError, match="属性upsert失败"):
                await attribute_repo.upsert(1, "新键", "新值")
    
    @pytest.mark.asyncio
    async def test_bulk_upsert_success(self, attribute_repo, mock_session, mock_attribute):
        """测试批量upsert - 成功"""
        # 创建多个属性
        attr1 = MagicMock()
        attr1.entity_id = 1
        attr1.key = "行业"
        attr1.value = "金融"
        
        attr2 = MagicMock()
        attr2.entity_id = 1
        attr2.key = "规模"
        attr2.value = "大型"
        
        attributes = {
            "行业": "金融",
            "规模": "大型"
        }
        
        # 模拟upsert方法
        with patch.object(attribute_repo, 'upsert', new_callable=AsyncMock) as mock_upsert:
            mock_upsert.side_effect = [attr1, attr2]
            
            # 执行测试
            result = await attribute_repo.bulk_upsert(1, attributes)
            
            # 验证结果
            assert result == [attr1, attr2]
            assert mock_upsert.call_count == 2
            mock_upsert.assert_any_call(1, "行业", "金融")
            mock_upsert.assert_any_call(1, "规模", "大型")
    
    @pytest.mark.asyncio
    async def test_bulk_upsert_empty_attributes(self, attribute_repo, mock_session):
        """测试批量upsert - 空属性字典"""
        # 执行测试
        result = await attribute_repo.bulk_upsert(1, {})
        
        # 验证结果
        assert result == []
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_bulk_upsert_database_error(self, attribute_repo, mock_session):
        """测试批量upsert - 数据库错误"""
        attributes = {
            "行业": "金融",
            "规模": "大型"
        }
        
        # 模拟upsert方法抛出异常
        with patch.object(attribute_repo, 'upsert', new_callable=AsyncMock) as mock_upsert:
            mock_upsert.side_effect = SQLAlchemyError("数据库错误")
            
            # 执行测试并验证异常
            with pytest.raises(DatabaseError, match="批量属性upsert失败"):
                await attribute_repo.bulk_upsert(1, attributes)
    
    @pytest.mark.asyncio
    async def test_delete_by_entity_success(self, attribute_repo, mock_session, mock_attribute):
        """测试删除实体属性 - 成功"""
        # 设置模拟结果
        attributes = [mock_attribute, mock_attribute]
        mock_result = self.create_awaitable_mock_result(scalars_value=attributes)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await attribute_repo.delete_by_entity(1)
        
        # 验证结果
        assert result == 2  # 删除了2个属性
        assert mock_session.execute.call_count == 1
        assert mock_session.delete.call_count == 2  # 删除了2个属性对象
    
    @pytest.mark.asyncio
    async def test_delete_by_entity_empty(self, attribute_repo, mock_session):
        """测试删除实体属性 - 空结果"""
        # 设置模拟结果
        mock_result = self.create_awaitable_mock_result(scalars_value=[])
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await attribute_repo.delete_by_entity(999)
        
        # 验证结果
        assert result == 0  # 删除了0个属性
        assert mock_session.execute.call_count == 1
        assert mock_session.delete.call_count == 0  # 没有删除任何属性对象
    
    @pytest.mark.asyncio
    async def test_delete_by_entity_database_error(self, attribute_repo, mock_session):
        """测试删除实体属性 - 数据库错误"""
        # 设置异常
        mock_session.execute.side_effect = SQLAlchemyError("数据库错误")
        
        # 执行测试并验证异常
        with pytest.raises(DatabaseError, match="删除实体属性失败"):
            await attribute_repo.delete_by_entity(1)
    
    @pytest.mark.asyncio
    async def test_upsert_create_new(self, attribute_repo, mock_session, mock_attribute):
        """测试upsert - 创建新属性"""
        # 设置模拟结果 - 属性不存在
        mock_result = self.create_mock_result(scalar_value=None)
        mock_session.execute.return_value = mock_result
        
        # 模拟create方法
        with patch.object(attribute_repo, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_attribute
            
            # 执行测试
            result = await attribute_repo.upsert(1, "新键", "新值")
            
            # 验证结果
            assert result is mock_attribute
            mock_create.assert_called_once_with(entity_id=1, key="新键", value="新值")