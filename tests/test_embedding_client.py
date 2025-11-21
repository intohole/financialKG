"""
Embedding 客户端测试
"""

import pytest
from unittest.mock import patch, MagicMock

from app.config.config_manager import ConfigManager
from app.embedding.embedding_client import EmbeddingClient
from app.embedding.exceptions import EmbeddingError


class TestEmbeddingClient:
    """
    EmbeddingClient 测试类
    """
    
    @pytest.fixture
    def mock_config_manager(self):
        """
        创建模拟的配置管理器
        """
        mock = MagicMock(spec=ConfigManager)
        # 模拟embedding配置
        mock_embedding_config = MagicMock()
        mock_embedding_config.model = "text-embedding-ada-002"
        mock_embedding_config.api_key = "test_api_key"
        mock_embedding_config.base_url = "https://api.example.com"
        mock_embedding_config.timeout = 30
        mock_embedding_config.max_retries = 3
        mock_embedding_config.dimension = 1536
        mock_embedding_config.normalize = True
        mock_embedding_config.secret_key = None
        mock_embedding_config.endpoint = None
        
        mock.get_embedding_config.return_value = mock_embedding_config
        return mock
    
    @pytest.fixture
    def embedding_client(self, mock_config_manager):
        """
        创建EmbeddingClient实例
        """
        # 使用patch避免实际调用第三方API
        with patch('app.embedding.embedding_client.OpenAIEmbeddings') as mock_openai_embeddings:
            # 配置mock的返回值
            mock_instance = MagicMock()
            mock_instance.embed_query.return_value = [0.1, 0.2, 0.3]  # 模拟嵌入向量
            mock_instance.embed_documents.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]  # 模拟批量嵌入
            mock_openai_embeddings.return_value = mock_instance
            
            client = EmbeddingClient(mock_config_manager)
            yield client
    
    def test_initialization(self, mock_config_manager):
        """
        测试客户端初始化
        """
        with patch('app.embedding.embedding_client.OpenAIEmbeddings'):
            client = EmbeddingClient(mock_config_manager)
            assert client is not None
            # 验证配置管理器的方法被调用
            mock_config_manager.get_embedding_config.assert_called_once()
    
    def test_embed_text(self, embedding_client):
        """
        测试单个文本嵌入
        """
        text = "这是一段测试文本"
        embedding = embedding_client.embed_text(text)
        
        # 验证返回值类型和内容
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_batch(self, embedding_client):
        """
        测试批量文本嵌入
        """
        texts = ["文本1", "文本2"]
        embeddings = embedding_client.embed_batch(texts)
        
        # 验证返回值类型和内容
        assert isinstance(embeddings, list)
        assert len(embeddings) == 2
        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            assert all(isinstance(x, float) for x in embedding)
    
    def test_get_config(self, embedding_client):
        """
        测试获取配置
        """
        config = embedding_client.get_config()
        
        # 验证配置包含必要的字段
        assert isinstance(config, dict)
        assert 'model' in config
        assert 'api_key' in config
        assert 'base_url' in config
    
    def test_refresh_config(self, embedding_client, mock_config_manager):
        """
        测试刷新配置
        """
        # 重置mock的调用次数
        mock_config_manager.get_embedding_config.reset_mock()
        
        # 调用刷新方法
        with patch('app.embedding.embedding_client.OpenAIEmbeddings'):
            embedding_client.refresh_config()
            # 验证配置管理器的方法被重新调用
            mock_config_manager.get_embedding_config.assert_called_once()
    
    def test_embed_text_error(self, embedding_client):
        """
        测试文本嵌入失败时的错误处理
        """
        # 修改mock以抛出异常
        with patch.object(embedding_client, '_embeddings') as mock_embeddings:
            mock_embeddings.embed_query.side_effect = Exception("API调用失败")
            
            # 验证异常被正确转换为EmbeddingError
            with pytest.raises(EmbeddingError):
                embedding_client.embed_text("测试文本")
    
    def test_embed_batch_error(self, embedding_client):
        """
        测试批量嵌入失败时的错误处理
        """
        # 修改mock以抛出异常
        with patch.object(embedding_client, '_embeddings') as mock_embeddings:
            mock_embeddings.embed_documents.side_effect = Exception("API调用失败")
            
            # 验证异常被正确转换为EmbeddingError
            with pytest.raises(EmbeddingError):
                embedding_client.embed_batch(["测试文本1", "测试文本2"])
