"""
配置管理器测试
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.config.config_manager import ConfigManager, ConfigError


class TestConfigManager:
    """配置管理器测试类"""
    
    @pytest.fixture
    def sample_config(self):
        """示例配置数据"""
        return {
            'llm': {
                'model': 'glm-4-flash',
                'api_key': 'test-key',
                'base_url': 'https://test.com',
                'timeout': 30,
                'max_retries': 3,
                'temperature': 0.1,
                'max_tokens': 2048
            },
            'database': {
                'url': 'sqlite+aiosqlite:///./test.db',
                'echo': False,
                'pool_pre_ping': True,
                'pool_recycle': 3600
            },
            'api': {
                'host': '127.0.0.1',
                'port': 8001,
                'debug': True,
                'reload': False,
                'workers': 2,
                'log_level': 'debug'
            }
        }
    
    @pytest.fixture
    def config_file(self, sample_config):
        """临时配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config, f)
            temp_path = f.name
        
        yield temp_path
        
        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def config_manager(self, config_file):
        """配置管理器实例"""
        return ConfigManager(config_file)
    
    def test_init_with_default_path(self):
        """测试使用默认路径初始化"""
        with patch('app.config.config_manager.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.parent = Path('/test')
            
            manager = ConfigManager()
            assert manager is not None
    
    def test_init_with_nonexistent_file(self):
        """测试初始化不存在的配置文件"""
        with pytest.raises(ConfigError, match="配置文件不存在"):
            ConfigManager("/nonexistent/config.yaml")
    
    def test_load_config_success(self, config_manager, sample_config):
        """测试成功加载配置"""
        config = config_manager.get_config()
        assert config == sample_config
    
    def test_load_config_invalid_yaml(self, config_file):
        """测试加载无效的YAML文件"""
        # 写入无效的YAML内容
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        manager = ConfigManager(config_file)
        with pytest.raises(ConfigError, match="YAML解析错误"):
            manager.get_config()
    
    def test_cache_mechanism(self, config_manager):
        """测试缓存机制"""
        # 第一次获取配置，会加载文件
        config1 = config_manager.get_config()
        
        # 第二次获取配置，应该使用缓存
        config2 = config_manager.get_config()
        
        assert config1 is config2  # 应该是同一个对象
    
    def test_reload_config(self, config_manager, sample_config):
        """测试重新加载配置"""
        # 获取初始配置
        config1 = config_manager.get_config()
        
        # 强制重新加载
        config_manager.reload()
        config2 = config_manager.get_config()
        
        assert config1 == config2  # 配置内容应该相同
    
    def test_get_llm_config(self, config_manager, sample_config):
        """测试获取大模型配置"""
        llm_config = config_manager.get_llm_config()
        
        assert llm_config.model == sample_config['llm']['model']
        assert llm_config.api_key == sample_config['llm']['api_key']
        assert llm_config.base_url == sample_config['llm']['base_url']
        assert llm_config.timeout == sample_config['llm']['timeout']
        assert llm_config.max_retries == sample_config['llm']['max_retries']
        assert llm_config.temperature == sample_config['llm']['temperature']
        assert llm_config.max_tokens == sample_config['llm']['max_tokens']
    
    def test_get_database_config(self, config_manager, sample_config):
        """测试获取数据库配置"""
        db_config = config_manager.get_database_config()
        
        assert db_config.url == sample_config['database']['url']
        assert db_config.echo == sample_config['database']['echo']
        assert db_config.pool_pre_ping == sample_config['database']['pool_pre_ping']
        assert db_config.pool_recycle == sample_config['database']['pool_recycle']
    
    def test_get_api_config(self, config_manager, sample_config):
        """测试获取API配置"""
        api_config = config_manager.get_api_config()
        
        assert api_config.host == sample_config['api']['host']
        assert api_config.port == sample_config['api']['port']
        assert api_config.debug == sample_config['api']['debug']
        assert api_config.reload == sample_config['api']['reload']
        assert api_config.workers == sample_config['api']['workers']
        assert api_config.log_level == sample_config['api']['log_level']
    
    def test_get_config_with_defaults(self, config_file):
        """测试获取配置时的默认值处理"""
        # 创建空配置文件
        with open(config_file, 'w') as f:
            yaml.dump({}, f)
        
        manager = ConfigManager(config_file)
        
        # 测试各种配置的默认值
        llm_config = manager.get_llm_config()
        assert llm_config.model == ''
        assert llm_config.timeout == 30
        
        db_config = manager.get_database_config()
        assert db_config.url == ''
        assert db_config.echo == False
        
        api_config = manager.get_api_config()
        assert api_config.host == '0.0.0.0'
        assert api_config.port == 8000
    
    def test_config_change_callback(self, config_manager):
        """测试配置变更回调"""
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        config_manager.add_change_callback(test_callback)
        config_manager.reload()
        
        assert callback_called
    
    def test_remove_config_change_callback(self, config_manager):
        """测试移除配置变更回调"""
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        config_manager.add_change_callback(test_callback)
        config_manager.remove_change_callback(test_callback)
        config_manager.reload()
        
        assert not callback_called
    
    def test_context_manager(self, config_file):
        """测试上下文管理器"""
        with patch.object(ConfigManager, 'start_watching') as mock_start:
            with patch.object(ConfigManager, 'stop_watching') as mock_stop:
                with ConfigManager(config_file) as manager:
                    assert manager is not None
                    mock_start.assert_called_once()
                
                mock_stop.assert_called_once()
    
    def test_file_modification_detection(self, config_manager, config_file, sample_config):
        """测试文件修改检测"""
        # 获取初始配置
        initial_config = config_manager.get_config()
        
        # 修改配置文件
        sample_config['llm']['model'] = 'new-model'
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        # 强制检查文件修改
        config_manager._last_modified = None
        new_config = config_manager.get_config()
        
        assert new_config['llm']['model'] == 'new-model'
    
    def test_environment_variable_override(self, config_file, sample_config):
        """测试环境变量覆盖"""
        with patch.dict(os.environ, {'CONFIG_PATH': config_file}):
            manager = ConfigManager()  # 应该使用环境变量指定的路径
            config = manager.get_config()
            assert config == sample_config
    
    def test_invalid_config_access(self, config_file):
        """测试无效的配置访问"""
        # 创建部分配置
        partial_config = {'llm': {'model': 'test'}}
        with open(config_file, 'w') as f:
            yaml.dump(partial_config, f)
        
        manager = ConfigManager(config_file)
        
        # 应该能处理缺失的配置项
        llm_config = manager.get_llm_config()
        assert llm_config.model == 'test'
        assert llm_config.api_key == ''  # 默认值
    
    def test_config_persistence_across_instances(self, config_file, sample_config):
        """测试配置在不同实例间的持久性"""
        manager1 = ConfigManager(config_file)
        manager2 = ConfigManager(config_file)
        
        config1 = manager1.get_config()
        config2 = manager2.get_config()
        
        assert config1 == config2 == sample_config