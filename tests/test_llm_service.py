"""
LLM Service 单元测试
测试大模型集成服务层的各项功能
"""

import pytest
from unittest import mock
from unittest.mock import AsyncMock
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.llm.llm_service import LLMService
from app.llm.llm_client import LLMClient
from app.llm.prompt_manager import PromptManager
from app.llm.base import LLMResponse
from app.exceptions.llm_exceptions import LLMError, GenerationError, PromptError


@pytest.fixture
def mock_llm_client():
    """模拟LLMClient"""
    mock_client = mock.Mock()
    # 使用与测试预期匹配的模型名称
    model_name = "gpt-3.5-turbo"
    
    # 模拟generate方法返回LLMResponse
    mock_client.generate.return_value = LLMResponse(
        content="Mock response",
        metadata={"model": model_name},
        tokens_used={"total": 100},
        latency=0.5
    )
    
    # 模拟批量生成方法
    mock_client.generate_batch.return_value = [
        LLMResponse(
            content="Mock batch response 0",
            metadata={"model": model_name},
            tokens_used={"total": 100},
            latency=0.5
        ),
        LLMResponse(
            content="Mock batch response 1",
            metadata={"model": model_name},
            tokens_used={"total": 100},
            latency=0.5
        ),
        LLMResponse(
            content="Mock batch response 2",
            metadata={"model": model_name},
            tokens_used={"total": 100},
            latency=0.5
        )
    ]
    
    # 模拟异步方法
    from unittest.mock import AsyncMock
    mock_client.generate_async = AsyncMock(return_value=LLMResponse(
        content="Mock async response",
        metadata={"model": model_name},
        tokens_used={"total": 100},
        latency=0.5
    ))
    
    mock_client.generate_batch_async = AsyncMock(return_value=[
        LLMResponse(
            content="Mock batch async response 0",
            metadata={"model": model_name},
            tokens_used={"total": 100},
            latency=0.5
        ),
        LLMResponse(
            content="Mock batch async response 1",
            metadata={"model": model_name},
            tokens_used={"total": 100},
            latency=0.5
        ),
        LLMResponse(
            content="Mock batch async response 2",
            metadata={"model": model_name},
            tokens_used={"total": 100},
            latency=0.5
        )
    ])
    
    # 模拟health_check方法
    mock_client.health_check.return_value = {
        'status': 'healthy',
        'model': model_name,
        'response_time': 0.5
    }
    
    # 模拟validate_template方法
    mock_client.validate_template.return_value = {"is_valid": True, "missing_variables": [], "extra_variables": []}
    
    # 模拟get_prompt_manager方法
    mock_prompt_manager = mock.Mock()
    mock_prompt_manager.get_all_prompts.return_value = ["template1", "template2"]
    mock_prompt_manager.get_prompt.side_effect = lambda template_name: "Test prompt template" if template_name in ["template1", "template2"] else None
    mock_client.get_prompt_manager.return_value = mock_prompt_manager
    
    # 确保mock_client有get_all_prompts方法
    mock_client.get_all_prompts.return_value = ["template1", "template2"]
    
    # 添加get_config方法
    mock_client.get_config.return_value = {"model": model_name}
    
    # 添加update_config方法
    mock_client.update_config.return_value = None
    
    return mock_client


@pytest.fixture
def mock_prompt_manager():
    """模拟PromptManager"""
    mock_pm = mock.MagicMock(spec=PromptManager)
    mock_pm.format_prompt.side_effect = lambda name, **kwargs: f"Formatted prompt: {name} with {kwargs}"
    return mock_pm


@pytest.fixture
def llm_service(mock_llm_client):
    """LLMService实例"""
    # 使用mock替代真实的LLMClient
    with mock.patch('app.llm.llm_service.LLMClient', return_value=mock_llm_client):
        # 清除单例状态以确保每次测试都是新实例
        LLMService._instance = None
        service = LLMService()
        yield service


class TestLLMService:
    """LLMService测试类"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # 清除之前的实例
        LLMService._instance = None
        
        # 创建两个实例
        service1 = LLMService()
        service2 = LLMService()
        
        # 验证是同一个实例
        assert service1 is service2
    
    def test_generate_text(self, llm_service, mock_llm_client):
        """测试生成文本"""
        # 调用generate_text
        result = llm_service.generate_text("Test prompt")
        
        # 验证调用
        mock_llm_client.generate.assert_called_once_with("Test prompt")
        
        # 验证结果
        assert result == "Mock response"
    
    def test_generate_text_with_template(self, llm_service, mock_llm_client, mock_prompt_manager):
        """测试使用模板生成文本"""
        # 调用generate_text_with_template
        result = llm_service.generate_text_with_template(
            "test_template",
            variable1="value1",
            variable2="value2"
        )
        
        # 验证提示词格式化
        mock_prompt_manager.format_prompt.assert_called_once_with(
            "test_template",
            variable1="value1",
            variable2="value2"
        )
        
        # 验证LLM调用
        formatted_prompt = mock_prompt_manager.format_prompt.return_value
        mock_llm_client.generate.assert_called_once_with(formatted_prompt)
        
        # 验证结果
        assert result == "Mock response"
    
    def test_generate_batch(self, llm_service, mock_llm_client):
        """测试批量生成"""
        # 设置mock返回值
        mock_responses = [
            LLMResponse(text=f"Response {i}", model="gpt-3.5-turbo")
            for i in range(3)
        ]
        mock_llm_client.generate_batch.return_value = mock_responses
        
        # 调用generate_batch
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        results = llm_service.generate_batch(prompts)
        
        # 验证调用
        mock_llm_client.generate_batch.assert_called_once_with(prompts)
        
        # 验证结果
        assert len(results) == 3
        assert results == ["Response 0", "Response 1", "Response 2"]
    
    def test_validate_template(self, llm_service, mock_prompt_manager):
        """测试验证模板"""
        # 设置mock返回值
        mock_prompt_manager.get_prompt.return_value = "Template with {var1} and {var2}"
        
        # 调用validate_template
        result = llm_service.validate_template("test_template", var1="value1", var2="value2")
        
        # 验证调用
        mock_prompt_manager.get_prompt.assert_called_once_with("test_template")
        
        # 验证结果
        assert result['is_valid'] is True
        assert result['missing_variables'] == []
        assert result['extra_variables'] == []
        
        # 测试缺少变量
        mock_prompt_manager.get_prompt.reset_mock()
        result = llm_service.validate_template("test_template", var1="value1")
        assert result['is_valid'] is False
        assert result['missing_variables'] == ["var2"]
        
        # 测试额外变量
        mock_prompt_manager.get_prompt.reset_mock()
        result = llm_service.validate_template(
            "test_template", 
            var1="value1", 
            var2="value2", 
            var3="value3"
        )
        assert result['extra_variables'] == ["var3"]
    
    def test_validate_template_nonexistent(self, llm_service, mock_prompt_manager):
        """测试验证不存在的模板"""
        # 模拟模板不存在
        mock_prompt_manager.get_prompt.side_effect = PromptError("Template not found")
        
        # 调用validate_template
        result = llm_service.validate_template("nonexistent_template")
        
        # 验证结果
        assert result['is_valid'] is False
        assert result['error'] == "Template not found"
    
    def test_get_available_templates(self, llm_service, mock_prompt_manager):
        """测试获取可用模板"""
        # 设置mock返回值
        mock_prompt_manager.get_all_prompts.return_value = [
            "template1", "template2", "subdir/template3"
        ]
        
        # 调用get_available_templates
        templates = llm_service.get_available_templates()
        
        # 验证调用
        mock_prompt_manager.get_all_prompts.assert_called_once()
        
        # 验证结果
        assert templates == ["template1", "template2", "subdir/template3"]
    
    def test_health_check(self, llm_service, mock_llm_client):
        """测试健康检查"""
        # 调用health_check
        result = llm_service.health_check()
        
        # 验证调用
        mock_llm_client.health_check.assert_called_once()
        
        # 验证结果
        assert result['status'] == 'healthy'
        assert result['model'] == 'gpt-3.5-turbo'
    
    def test_get_stats(self, llm_service, mock_llm_client):
        """测试获取统计信息"""
        # 设置调用历史
        llm_service._call_history = [
            {"timestamp": 1000, "model": "gpt-3.5-turbo", "tokens": 100, "success": True},
            {"timestamp": 1001, "model": "gpt-3.5-turbo", "tokens": 200, "success": True},
            {"timestamp": 1002, "model": "gpt-3.5-turbo", "tokens": 50, "success": False}
        ]
        
        # 调用get_stats
        stats = llm_service.get_stats()
        
        # 验证结果
        assert stats['total_calls'] == 3
        assert stats['successful_calls'] == 2
        assert stats['failed_calls'] == 1
        assert stats['total_tokens'] == 350
        assert stats['success_rate'] == (2/3 * 100)  # 约66.67%
    
    def test_clear_stats(self, llm_service):
        """测试清除统计信息"""
        # 设置调用历史
        llm_service._call_history = [
            {"timestamp": 1000, "model": "gpt-3.5-turbo", "tokens": 100, "success": True}
        ]
        
        # 清除统计
        llm_service.clear_stats()
        
        # 验证
        assert len(llm_service._call_history) == 0
        stats = llm_service.get_stats()
        assert stats['total_calls'] == 0
    
    @pytest.mark.asyncio
    async def test_generate_text_async(self, llm_service, mock_llm_client):
        """测试异步生成文本"""
        # 调用generate_text_async
        result = await llm_service.generate_text_async("Test prompt")
        
        # 验证调用
        mock_llm_client.generate.assert_called_once_with("Test prompt")
        
        # 验证结果
        assert result == "Mock response"
    
    @pytest.mark.asyncio
    async def test_generate_batch_async(self, llm_service, mock_llm_client):
        """测试异步批量生成"""
        # 设置mock返回值
        mock_responses = [
            LLMResponse(text=f"Response {i}", model="gpt-3.5-turbo")
            for i in range(3)
        ]
        mock_llm_client.generate_batch.return_value = mock_responses
        
        # 调用generate_batch_async
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        results = await llm_service.generate_batch_async(prompts)
        
        # 验证结果
        assert len(results) == 3
        assert results == ["Response 0", "Response 1", "Response 2"]
    
    def test_error_handling(self, llm_service, mock_llm_client):
        """测试错误处理"""
        # 模拟生成错误
        mock_llm_client.generate.side_effect = GenerationError("Generation failed")
        
        # 验证异常传递
        with pytest.raises(GenerationError):
            llm_service.generate_text("Test prompt")
    
    def test_custom_executor(self):
        """测试自定义线程池执行器"""
        # 创建自定义执行器
        custom_executor = ThreadPoolExecutor(max_workers=10)
        
        # 清除单例状态
        LLMService._instance = None
        
        try:
            # 使用自定义执行器创建服务
            with mock.patch('app.llm.llm_service.LLMClient'):
                with mock.patch('app.llm.llm_service.PromptManager'):
                    service = LLMService(executor=custom_executor)
                    assert service._executor == custom_executor
        finally:
            # 清理
            custom_executor.shutdown(wait=False)
    
    def test_context_management(self):
        """测试上下文管理"""
        # 清除单例状态
        LLMService._instance = None
        
        # 使用上下文管理器
        with mock.patch('app.llm.llm_service.LLMClient'):
            with mock.patch('app.llm.llm_service.PromptManager'):
                with LLMService() as service:
                    assert service is not None
    
    def test_update_call_history(self, llm_service):
        """测试更新调用历史"""
        # 记录成功调用
        llm_service._update_call_history(
            model="gpt-3.5-turbo",
            tokens=100,
            success=True
        )
        
        # 记录失败调用
        llm_service._update_call_history(
            model="gpt-3.5-turbo",
            tokens=50,
            success=False
        )
        
        # 验证历史记录
        assert len(llm_service._call_history) == 2
        assert llm_service._call_history[0]['success'] is True
        assert llm_service._call_history[1]['success'] is False
    
    def test_extract_variables_from_template(self, llm_service):
        """测试从模板提取变量"""
        # 测试基本变量提取
        variables = llm_service._extract_variables_from_template("Hello {name}, you are {age} years old")
        assert sorted(variables) == sorted(["name", "age"])
        
        # 测试无变量的模板
        variables = llm_service._extract_variables_from_template("Fixed template with no variables")
        assert variables == []
        
        # 测试重复变量
        variables = llm_service._extract_variables_from_template("Repeat {var} and {var} again")
        assert variables == ["var"]  # 应该去重
        
        # 测试复杂变量名
        variables = llm_service._extract_variables_from_template("Complex {var_name_123} and {_var}")
        assert sorted(variables) == sorted(["var_name_123", "_var"])