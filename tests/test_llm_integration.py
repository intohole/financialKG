"""
大模型集成测试
使用真实配置和实际的大模型服务进行集成测试
"""

import pytest
import os
import asyncio
from pathlib import Path
from unittest import mock

from app.llm.llm_client import LLMClient
from app.llm.llm_service import LLMService
from app.llm.base import LLMResponse
from app.llm.exceptions import (
    GenerationError,
    ConfigurationError,
    ServiceUnavailableError,
    RateLimitError
)
from app.config.config_manager import ConfigManager


class TestLLMIntegration:
    """
    大模型集成测试类
    使用项目配置文件中的真实配置进行测试
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """
        测试设置
        确保使用项目根目录下的配置文件
        """
        # 确保配置文件存在
        self.config_path = Path(__file__).parent.parent / 'config.yaml'
        assert self.config_path.exists(), f"配置文件不存在: {self.config_path}"
        
        # 创建提示词目录（如果不存在）
        self.prompt_dir = Path(__file__).parent.parent / 'prompt'
        self.prompt_dir.mkdir(exist_ok=True)
        
        # 创建测试提示词文件
        self._create_test_prompt()
        
        yield
        
        # 清理测试提示词文件
        self._cleanup_test_prompt()
    
    def _create_test_prompt(self):
        """
        创建测试提示词文件
        """
        test_prompt_content = """
        请用简洁的语言回答以下问题：
        
        {question}
        """
        
        test_prompt_file = self.prompt_dir / 'test_prompt.txt'
        with open(test_prompt_file, 'w', encoding='utf-8') as f:
            f.write(test_prompt_content)
    
    def _cleanup_test_prompt(self):
        """
        清理测试提示词文件
        """
        test_prompt_file = self.prompt_dir / 'test_prompt.txt'
        if test_prompt_file.exists():
            test_prompt_file.unlink()
    
    def test_config_manager_loading(self):
        """
        测试配置管理器能否正确加载真实配置
        """
        config_manager = ConfigManager(config_path=self.config_path)
        llm_config = config_manager.get_llm_config()
        
        # 验证配置加载
        assert llm_config.model == "glm-4-flash"
        assert llm_config.api_key == "9f0867c6ca528cfb0faa3ea170411448.YpruqxYPsTnpyrjM"
        assert llm_config.base_url == "https://open.bigmodel.cn/api/paas/v4/"
        assert llm_config.temperature == 0.1
        assert llm_config.max_tokens == 2048
    
    def test_llm_client_initialization_with_real_config(self):
        """
        测试使用真实配置初始化LLMClient
        """
        # 使用项目配置初始化客户端
        client = LLMClient()
        
        # 验证客户端初始化成功
        assert client is not None
        assert client.get_config()['model'] == "glm-4-flash"
        assert client.get_prompt_manager() is not None
    
    def test_simple_text_generation(self):
        """
        测试简单文本生成功能
        注意：此测试会调用真实的大模型API，请确保API密钥有效
        """
        # 由于调用真实API可能会失败，我们使用try-except捕获异常
        try:
            client = LLMClient()
            response = client.generate("请简要介绍什么是人工智能")
            
            # 验证响应格式
            assert isinstance(response, LLMResponse)
            assert response.content is not None
            assert len(response.content.strip()) > 0
            assert response.metadata['model'] == "glm-4-flash"
            print(f"\n简单生成测试成功，响应内容: {response.content[:100]}...")
            
        except RateLimitError:
            pytest.skip("跳过测试：达到API速率限制")
        except ServiceUnavailableError:
            pytest.skip("跳过测试：服务不可用")
        except (GenerationError, ConfigurationError) as e:
            print(f"警告：大模型调用失败: {e}")
            # 如果是配置错误，可能是API密钥无效或过期
            if "API key is invalid" in str(e) or "authentication" in str(e).lower():
                pytest.skip("跳过测试：API密钥无效或认证失败")
            else:
                raise
    
    def test_prompt_template_usage(self):
        """
        测试使用提示词模板生成文本
        """
        try:
            client = LLMClient()
            response = client.generate_from_template(
                prompt_name="test_prompt",
                question="金融知识图谱的主要应用场景是什么？"
            )
            
            # 验证响应
            assert isinstance(response, LLMResponse)
            assert response.content is not None
            assert len(response.content.strip()) > 0
            print(f"\n模板生成测试成功，响应内容: {response.content[:100]}...")
            
        except RateLimitError:
            pytest.skip("跳过测试：达到API速率限制")
        except ServiceUnavailableError:
            pytest.skip("跳过测试：服务不可用")
        except (GenerationError, ConfigurationError) as e:
            print(f"警告：大模型调用失败: {e}")
            if "API key is invalid" in str(e) or "authentication" in str(e).lower():
                pytest.skip("跳过测试：API密钥无效或认证失败")
            else:
                raise
    
    def test_llm_service_integration(self):
        """
        测试LLMService的集成功能
        """
        try:
            # 获取LLMService实例（单例模式）
            service = LLMService()
            
            # 测试简单生成
            response = service.generate("1+1等于多少？")
            assert isinstance(response, LLMResponse)
            assert len(response.content.strip()) > 0
            print(f"\n服务层生成测试成功，响应内容: {response.content[:100]}...")
            
            # 测试健康检查
            health_status = service.health_check()
            print(f"\n健康检查状态: {health_status}")
            
            # 注释掉统计信息调用，因为LLMService类中没有这个方法
            # stats = service.get_stats()
            # print(f"\n调用统计: {stats}")
            
        except RateLimitError:
            pytest.skip("跳过测试：达到API速率限制")
        except ServiceUnavailableError:
            pytest.skip("跳过测试：服务不可用")
        except Exception as e:
            print(f"警告：服务层测试失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_async_text_generation(self):
        """
        测试异步文本生成功能
        """
        try:
            service = LLMService()
            response = await service.async_generate("请用一个词描述人工智能")
            
            assert isinstance(response, LLMResponse)
            assert len(response.content.strip()) > 0
            print(f"\n异步生成测试成功，响应内容: {response.content}")
            
        except RateLimitError:
            pytest.skip("跳过测试：达到API速率限制")
        except ServiceUnavailableError:
            pytest.skip("跳过测试：服务不可用")
        except Exception as e:
            print(f"警告：异步测试失败: {e}")
            raise


# 条件运行器：如果环境变量SKIP_INTEGRATION_TESTS为True，则跳过所有集成测试
# 这样可以在CI/CD环境中选择性地运行集成测试
if os.environ.get('SKIP_INTEGRATION_TESTS') == 'True':
    for name in dir(TestLLMIntegration):
        if name.startswith('test_') and callable(getattr(TestLLMIntegration, name)):
            setattr(TestLLMIntegration, name, pytest.mark.skip(reason="集成测试已禁用")(getattr(TestLLMIntegration, name)))


if __name__ == '__main__':
    # 直接运行测试
    pytest.main(['-xvs', __file__])
