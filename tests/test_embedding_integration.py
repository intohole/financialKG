"""
Embedding服务集成测试
"""

import pytest
from unittest.mock import patch, MagicMock
import os

from app.config.config_manager import ConfigManager, EmbeddingConfig
from app.embedding.embedding_service import EmbeddingService
from app.embedding.embedding_client import EmbeddingClient


class TestEmbeddingIntegration:
    """
    Embedding服务集成测试类
    """
    
    @pytest.fixture
    def mock_config(self):
        """
        创建模拟的配置数据
        """
        return {
            "embedding": {
                "model": "text-embedding-ada-002",
                "api_key": "test-api-key",
                "base_url": "https://api.openai.com/v1",
                "timeout": 30,
                "max_retries": 3,
                "dimension": 1536,
                "normalize": True
            },
            "cache": {
                "max_size": 1000
            }
        }
    
    @pytest.fixture
    def mock_config_manager(self, mock_config):
        """
        创建模拟的配置管理器
        """
        # 创建EmbeddingConfig实例
        mock_embedding_config = EmbeddingConfig(
            model="text-embedding-ada-002",
            api_key="test-api-key",
            base_url="https://api.openai.com/v1",
            timeout=30,
            max_retries=3,
            dimension=1536,
            normalize=True
        )
        
        # 创建缓存配置
        mock_cache_config = MagicMock()
        mock_cache_config.max_size = 1000
        
        # 设置配置管理器
        mock = MagicMock(spec=ConfigManager)
        mock.get_embedding_config.return_value = mock_embedding_config
        mock.get_cache_config.return_value = mock_cache_config
        mock.refresh_config = MagicMock()
        
        return mock
    
    @pytest.fixture
    def mock_embedding_client(self):
        """
        创建模拟的嵌入客户端
        """
        mock = MagicMock(spec=EmbeddingClient)
        mock.embed_text.return_value = [0.1, 0.2, 0.3]
        mock.embed_batch.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        return mock
    
    def test_embedding_service_with_config(self, mock_config_manager, mock_embedding_client):
        """
        测试EmbeddingService正确使用配置管理器中的配置
        """
        # 清除单例实例
        EmbeddingService._instance = None
        
        # 使用patch替换EmbeddingClient
        with patch('app.embedding.embedding_service.EmbeddingClient', return_value=mock_embedding_client) as mock_client_class:
            # 创建服务实例
            service = EmbeddingService(mock_config_manager)
            
            # 验证EmbeddingClient被正确初始化，配置管理器作为参数传递
            mock_client_class.assert_called_once_with(mock_config_manager)
            
            # 测试embed_text方法
            text = "集成测试文本"
            embedding = service.embed_text(text)
            
            # 验证返回值
            assert embedding == [0.1, 0.2, 0.3]
            # 验证客户端方法被调用
            mock_embedding_client.embed_text.assert_called_once_with(text)
    
    def test_embedding_client_uses_embedding_config(self, mock_config_manager):
        """
        测试EmbeddingClient正确使用embedding配置
        """
        # 创建客户端实例
        client = EmbeddingClient(mock_config_manager)
        
        # 验证get_embedding_config被调用
        mock_config_manager.get_embedding_config.assert_called_once()
    
    def test_refresh_config(self, mock_config_manager, mock_embedding_client):
        """
        测试刷新配置功能
        """
        # 清除单例实例
        EmbeddingService._instance = None
        
        # 创建服务实例
        with patch('app.embedding.embedding_service.EmbeddingClient', return_value=mock_embedding_client):
            service = EmbeddingService(mock_config_manager)
            
            # 调用refresh_config方法
            service.refresh_config()
            
            # 验证配置管理器的refresh_config方法被调用
            mock_config_manager.refresh_config.assert_called_once()
    
    def test_embedding_service_with_llm_config_fallback(self):
        """
        测试当没有embedding配置时，回退到使用llm配置
        """
        # 创建只有llm配置的配置管理器
        mock_config_manager = MagicMock(spec=ConfigManager)
        
        # 模拟get_embedding_config引发异常（表示没有embedding配置）
        mock_config_manager.get_embedding_config.side_effect = Exception("No embedding config")
        
        # 模拟llm配置
        mock_llm_config = MagicMock()
        mock_llm_config.model = "glm-4-flash"
        mock_llm_config.api_key = "fallback-api-key"
        mock_llm_config.base_url = "https://api.example.com"
        mock_config_manager.get_llm_config.return_value = mock_llm_config
        
        # 模拟缓存配置
        mock_cache_config = MagicMock()
        mock_cache_config.max_size = 1000
        mock_config_manager.get_cache_config.return_value = mock_cache_config
        
        # 清除单例实例
        EmbeddingService._instance = None
        
        # 创建服务实例
        with patch('app.embedding.embedding_service.EmbeddingClient') as mock_client_class:
            service = EmbeddingService(mock_config_manager)
            
            # 验证get_embedding_config被调用
            mock_config_manager.get_embedding_config.assert_called_once()
            # 验证get_llm_config被调用作为回退
            mock_config_manager.get_llm_config.assert_called_once()
    
    def test_embedding_service_error_handling(self, mock_config_manager):
        """
        测试错误处理
        """
        # 模拟get_embedding_config和get_llm_config都引发异常
        mock_config_manager.get_embedding_config.side_effect = Exception("No embedding config")
        mock_config_manager.get_llm_config.side_effect = Exception("No llm config")
        
        # 清除单例实例
        EmbeddingService._instance = None
        
        # 验证创建服务实例时引发异常
        with pytest.raises(Exception):
            EmbeddingService(mock_config_manager)
