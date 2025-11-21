"""
Embedding 服务测试
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.config.config_manager import ConfigManager
from app.embedding.embedding_service import EmbeddingService
from app.embedding.embedding_client import EmbeddingClient
from app.embedding.exceptions import EmbeddingError


class TestEmbeddingService:
    """
    EmbeddingService 测试类
    """
    
    @pytest.fixture
    def mock_config_manager(self):
        """
        创建模拟的配置管理器
        """
        mock = MagicMock(spec=ConfigManager)
        # 模拟缓存配置
        mock_cache_config = MagicMock()
        mock_cache_config.max_size = 1000
        mock.get_cache_config.return_value = mock_cache_config
        return mock
    
    @pytest.fixture
    def mock_embedding_client(self):
        """
        创建模拟的嵌入客户端
        """
        mock = MagicMock(spec=EmbeddingClient)
        mock.embed_text.return_value = [0.1, 0.2, 0.3]
        mock.embed_batch.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock.get_config.return_value = {'model': 'text-embedding-ada-002'}
        return mock
    
    @pytest.fixture
    def embedding_service(self, mock_config_manager, mock_embedding_client):
        """
        创建EmbeddingService实例
        """
        # 清除单例实例，确保每次测试都是新的实例
        EmbeddingService._instance = None
        
        # 使用patch替换EmbeddingClient
        with patch('app.embedding.embedding_service.EmbeddingClient', return_value=mock_embedding_client):
            service = EmbeddingService(mock_config_manager)
            yield service
    
    def test_singleton_pattern(self, mock_config_manager):
        """
        测试单例模式
        """
        # 清除单例实例
        EmbeddingService._instance = None
        
        with patch('app.embedding.embedding_service.EmbeddingClient'):
            service1 = EmbeddingService(mock_config_manager)
            service2 = EmbeddingService(mock_config_manager)
            
            # 验证两个实例是同一个对象
            assert service1 is service2
    
    def test_embed_text(self, embedding_service, mock_embedding_client):
        """
        测试单个文本嵌入
        """
        text = "这是一段测试文本"
        embedding = embedding_service.embed_text(text)
        
        # 验证客户端方法被调用
        mock_embedding_client.embed_text.assert_called_once_with(text)
        # 验证返回值
        assert embedding == [0.1, 0.2, 0.3]
    
    def test_embed_text_cache(self, embedding_service, mock_embedding_client):
        """
        测试文本嵌入缓存功能
        """
        text = "缓存测试文本"
        
        # 第一次调用，应该调用客户端
        embedding1 = embedding_service.embed_text(text)
        mock_embedding_client.embed_text.assert_called_once_with(text)
        
        # 重置调用次数
        mock_embedding_client.embed_text.reset_mock()
        
        # 第二次调用，应该使用缓存，不调用客户端
        embedding2 = embedding_service.embed_text(text)
        mock_embedding_client.embed_text.assert_not_called()
        
        # 验证两次返回值相同
        assert embedding1 == embedding2
    
    def test_embed_batch(self, embedding_service, mock_embedding_client):
        """
        测试批量文本嵌入
        """
        texts = ["文本1", "文本2"]
        embeddings = embedding_service.embed_batch(texts)
        
        # 验证客户端方法被调用
        mock_embedding_client.embed_batch.assert_called_once()
        # 验证返回值
        assert len(embeddings) == 2
    
    def test_embed_batch_cache(self, embedding_service, mock_embedding_client):
        """
        测试批量文本嵌入缓存功能
        """
        texts = ["批量缓存1", "批量缓存2"]
        
        # 第一次调用，应该调用客户端
        embeddings1 = embedding_service.embed_batch(texts)
        mock_embedding_client.embed_batch.assert_called_once()
        
        # 重置调用次数
        mock_embedding_client.embed_batch.reset_mock()
        
        # 第二次调用，应该使用缓存，不调用客户端
        embeddings2 = embedding_service.embed_batch(texts)
        mock_embedding_client.embed_batch.assert_not_called()
        
        # 验证两次返回值相同
        assert embeddings1 == embeddings2
    
    def test_embed_text_no_cache(self, embedding_service, mock_embedding_client):
        """
        测试禁用缓存的情况
        """
        text = "不使用缓存的文本"
        
        # 第一次调用，应该调用客户端
        embedding1 = embedding_service.embed_text(text, use_cache=False)
        mock_embedding_client.embed_text.assert_called_once_with(text)
        
        # 重置调用次数
        mock_embedding_client.embed_text.reset_mock()
        
        # 第二次调用，仍然应该调用客户端
        embedding2 = embedding_service.embed_text(text, use_cache=False)
        mock_embedding_client.embed_text.assert_called_once_with(text)
    
    @pytest.mark.asyncio
    async def test_aembed_text(self, embedding_service, mock_embedding_client):
        """
        测试异步单个文本嵌入
        """
        text = "异步测试文本"
        
        # 使用asyncio.to_thread的mock
        with patch('asyncio.to_thread', return_value=[0.1, 0.2, 0.3]) as mock_to_thread:
            embedding = await embedding_service.aembed_text(text)
            
            # 验证to_thread被调用
            mock_to_thread.assert_called_once()
            # 验证返回值
            assert embedding == [0.1, 0.2, 0.3]
    
    @pytest.mark.asyncio
    async def test_aembed_batch(self, embedding_service, mock_embedding_client):
        """
        测试异步批量文本嵌入
        """
        texts = ["异步文本1", "异步文本2"]
        
        # 使用asyncio.to_thread的mock
        with patch('asyncio.to_thread', return_value=[[0.1, 0.2], [0.3, 0.4]]) as mock_to_thread:
            embeddings = await embedding_service.aembed_batch(texts)
            
            # 验证to_thread被调用
            mock_to_thread.assert_called_once()
            # 验证返回值
            assert len(embeddings) == 2
    
    def test_calculate_similarity(self, embedding_service):
        """
        测试相似度计算
        """
        embedding1 = [1.0, 2.0, 3.0]
        embedding2 = [1.0, 2.0, 3.0]  # 相同向量，相似度应该为1
        
        similarity = embedding_service.calculate_similarity(embedding1, embedding2)
        
        # 验证相似度为1.0
        assert similarity == pytest.approx(1.0)
        
        # 测试正交向量，相似度应该为0
        embedding3 = [1.0, 0.0, 0.0]
        embedding4 = [0.0, 1.0, 0.0]
        similarity = embedding_service.calculate_similarity(embedding3, embedding4)
        assert similarity == pytest.approx(0.0)
    
    def test_clear_cache(self, embedding_service):
        """
        测试清空缓存
        """
        text = "要缓存的文本"
        
        # 先缓存一个文本
        embedding_service.embed_text(text)
        
        # 清空缓存
        embedding_service.clear_cache()
        
        # 验证缓存被清空（可以通过检查缓存字典大小，但这里我们通过重新调用方法并验证客户端被再次调用来间接验证）
        with patch.object(embedding_service, '_client') as mock_client:
            mock_client.embed_text.return_value = [0.1, 0.2, 0.3]
            embedding_service.embed_text(text)
            mock_client.embed_text.assert_called_once()
    
    def test_get_stats(self, embedding_service):
        """
        测试获取统计信息
        """
        stats = embedding_service.get_stats()
        
        # 验证统计信息包含必要字段
        assert isinstance(stats, dict)
        assert 'cache_size' in stats
        assert 'max_cache_size' in stats
        assert 'model' in stats
    
    def test_embed_text_empty(self, embedding_service):
        """
        测试空文本输入
        """
        with pytest.raises(EmbeddingError):
            embedding_service.embed_text("")
        
        with pytest.raises(EmbeddingError):
            embedding_service.embed_text("   ")  # 只有空白字符
    
    def test_embed_batch_empty(self, embedding_service):
        """
        测试空文本列表输入
        """
        with pytest.raises(EmbeddingError):
            embedding_service.embed_batch([])
