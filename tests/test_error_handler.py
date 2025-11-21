"""
错误处理器单元测试
测试错误处理、重试策略和异常转换功能
"""

import time
import pytest
from unittest import mock

from app.llm.error_handler import (
    ErrorHandler, 
    RetryConfig,
    error_handler,
    retry_on_llm_error,
    safe_llm_call
)
from app.llm.exceptions import (
    LLMError,
    GenerationError,
    ConfigurationError,
    RateLimitError,
    AuthenticationError,
    ServiceUnavailableError,
    PromptError
)


@pytest.fixture
def custom_error_handler():
    """自定义错误处理器"""
    retry_config = RetryConfig(
        max_retries=2,
        base_delay=0.1,
        max_delay=1.0,
        backoff_factor=2.0
    )
    return ErrorHandler(default_retry_config=retry_config)


class TestErrorHandler:
    """错误处理器测试类"""
    
    def test_handle_error_llm_error(self, custom_error_handler):
        """测试处理LLMError异常"""
        # 创建LLMError
        original_error = GenerationError("生成失败")
        
        # 处理异常
        handled_error = custom_error_handler.handle_error(original_error)
        
        # 验证返回相同的异常
        assert handled_error is original_error
        assert isinstance(handled_error, GenerationError)
    
    def test_handle_error_authentication(self, custom_error_handler):
        """测试处理认证错误"""
        # 创建原始异常
        original_error = Exception("Invalid API key provided")
        
        # 处理异常
        handled_error = custom_error_handler.handle_error(original_error)
        
        # 验证转换为AuthenticationError
        assert isinstance(handled_error, AuthenticationError)
        assert "认证失败" in str(handled_error)
    
    def test_handle_error_rate_limit(self, custom_error_handler):
        """测试处理速率限制错误"""
        # 创建原始异常
        original_error = Exception("Rate limit exceeded, retry after 60")
        
        # 处理异常
        handled_error = custom_error_handler.handle_error(original_error)
        
        # 验证转换为RateLimitError
        assert isinstance(handled_error, RateLimitError)
        assert "速率限制" in str(handled_error)
        assert handled_error.retry_after == 60
    
    def test_handle_error_service_unavailable(self, custom_error_handler):
        """测试处理服务不可用错误"""
        # 创建原始异常
        original_error = Exception("Service unavailable due to maintenance")
        context = {"service": "openai"}
        
        # 处理异常
        handled_error = custom_error_handler.handle_error(original_error, context)
        
        # 验证转换为ServiceUnavailableError
        assert isinstance(handled_error, ServiceUnavailableError)
        assert "服务不可用" in str(handled_error)
        assert handled_error.service == "openai"
    
    def test_handle_error_configuration(self, custom_error_handler):
        """测试处理配置错误"""
        # 创建原始异常
        original_error = Exception("Invalid configuration parameter")
        context = {"config_key": "model"}
        
        # 处理异常
        handled_error = custom_error_handler.handle_error(original_error, context)
        
        # 验证转换为ConfigurationError
        assert isinstance(handled_error, ConfigurationError)
        assert "配置错误" in str(handled_error)
        assert handled_error.config_key == "model"
    
    def test_handle_error_prompt(self, custom_error_handler):
        """测试处理提示词错误"""
        # 创建原始异常
        original_error = Exception("Missing variable in prompt template")
        context = {"prompt_name": "test_template"}
        
        # 处理异常
        handled_error = custom_error_handler.handle_error(original_error, context)
        
        # 验证转换为PromptError
        assert isinstance(handled_error, PromptError)
        assert "提示词错误" in str(handled_error)
        assert handled_error.prompt_name == "test_template"
    
    def test_handle_error_default(self, custom_error_handler):
        """测试默认错误处理"""
        # 创建原始异常
        original_error = Exception("Unknown error occurred")
        context = {"model": "gpt-3.5-turbo"}
        
        # 处理异常
        handled_error = custom_error_handler.handle_error(original_error, context)
        
        # 验证默认转换为GenerationError
        assert isinstance(handled_error, GenerationError)
        assert "生成失败" in str(handled_error)
        assert handled_error.model == "gpt-3.5-turbo"
    
    def test_handle_error_nested_exception(self, custom_error_handler):
        """测试处理嵌套异常"""
        # 创建导致错误处理失败的异常
        with mock.patch.object(custom_error_handler, '_extract_retry_after') as mock_extract:
            mock_extract.side_effect = Exception("Extraction failed")
            
            # 处理异常
            original_error = Exception("Rate limit exceeded")
            handled_error = custom_error_handler.handle_error(original_error)
            
            # 验证返回LLMError
            assert isinstance(handled_error, LLMError)
    
    def test_should_retry(self, custom_error_handler):
        """测试是否应该重试"""
        # 可重试的异常
        retryable_exceptions = [
            GenerationError("生成失败"),
            RateLimitError("速率限制"),
            ServiceUnavailableError("服务不可用")
        ]
        
        for exc in retryable_exceptions:
            assert custom_error_handler.should_retry(exc)
        
        # 不可重试的异常
        non_retryable_exceptions = [
            AuthenticationError("认证失败"),
            ConfigurationError("配置错误"),
            PromptError("提示词错误")
        ]
        
        for exc in non_retryable_exceptions:
            assert not custom_error_handler.should_retry(exc)
    
    def test_should_retry_with_config(self, custom_error_handler):
        """测试使用自定义配置判断是否重试"""
        # 创建自定义重试配置
        retry_config = RetryConfig(
            retry_on_exceptions=[ValueError],
            retry_on_messages=["retry this"]
        )
        
        # 测试异常类型匹配
        assert custom_error_handler.should_retry(ValueError("test"), retry_config)
        
        # 测试错误消息匹配
        assert custom_error_handler.should_retry(Exception("Please retry this error"), retry_config)
        
        # 测试不匹配
        assert not custom_error_handler.should_retry(TypeError("wrong type"), retry_config)
    
    def test_get_retry_delay(self, custom_error_handler):
        """测试计算重试延迟"""
        # 测试基本延迟计算
        assert custom_error_handler.get_retry_delay(1) == 0.1  # 第1次重试
        assert custom_error_handler.get_retry_delay(2) == 0.2  # 第2次重试
        assert custom_error_handler.get_retry_delay(3) == 0.4  # 第3次重试
        
        # 测试最大延迟限制
        custom_config = RetryConfig(max_delay=0.3)
        assert custom_error_handler.get_retry_delay(3, custom_config) == 0.3  # 应该被限制
    
    @mock.patch('time.sleep')
    def test_retry_decorator_success(self, mock_sleep, custom_error_handler):
        """测试重试装饰器 - 成功情况"""
        # 创建测试函数
        @custom_error_handler.retry()
        def test_function(success_on_attempt=1):
            test_function.attempts = getattr(test_function, 'attempts', 0) + 1
            if test_function.attempts < success_on_attempt:
                raise GenerationError("Attempt failed")
            return "Success"
        
        # 测试第一次尝试就成功
        test_function.attempts = 0
        result = test_function(success_on_attempt=1)
        assert result == "Success"
        assert test_function.attempts == 1
        mock_sleep.assert_not_called()
        
        # 测试在第二次尝试成功
        test_function.attempts = 0
        result = test_function(success_on_attempt=2)
        assert result == "Success"
        assert test_function.attempts == 2
        assert mock_sleep.call_count == 1
    
    @mock.patch('time.sleep')
    def test_retry_decorator_exhaustion(self, mock_sleep, custom_error_handler):
        """测试重试装饰器 - 重试耗尽"""
        # 创建总是失败的测试函数
        @custom_error_handler.retry()
        def failing_function():
            raise GenerationError("Always fails")
        
        # 验证抛出异常
        with pytest.raises(GenerationError) as exc_info:
            failing_function()
        
        # 验证重试次数
        assert mock_sleep.call_count == 2  # 重试配置中的max_retries
        assert "达到最大重试次数" in str(exc_info.value)
    
    @mock.patch('time.sleep')
    def test_retry_decorator_non_retryable(self, mock_sleep, custom_error_handler):
        """测试重试装饰器 - 不可重试的异常"""
        # 创建抛出不可重试异常的函数
        @custom_error_handler.retry()
        def non_retryable_function():
            raise AuthenticationError("Auth failed")
        
        # 验证直接抛出异常，不重试
        with pytest.raises(AuthenticationError):
            non_retryable_function()
        
        # 验证没有调用sleep
        mock_sleep.assert_not_called()
    
    def test_catch_and_log_decorator(self, custom_error_handler):
        """测试异常捕获和日志记录装饰器"""
        # 创建测试函数
        @custom_error_handler.catch_and_log(fallback_value="Fallback")
        def error_function():
            raise Exception("Test error")
        
        # 测试异常被捕获并返回回退值
        result = error_function()
        assert result == "Fallback"
    
    def test_catch_and_log_decorator_re_raise(self, custom_error_handler):
        """测试异常捕获装饰器 - 重新抛出"""
        # 创建测试函数
        @custom_error_handler.catch_and_log(re_raise=True)
        def re_raise_function():
            raise Exception("Test error")
        
        # 测试异常被重新抛出
        with pytest.raises(LLMError):
            re_raise_function()
    
    def test_validate_arguments_decorator(self, custom_error_handler):
        """测试参数验证装饰器"""
        # 创建测试函数
        @custom_error_handler.validate_arguments(
            age=lambda x: isinstance(x, int) and x > 0,
            name=lambda x: isinstance(x, str) and len(x) > 0
        )
        def validate_function(name, age):
            return f"{name} is {age} years old"
        
        # 测试有效参数
        result = validate_function(name="John", age=30)
        assert result == "John is 30 years old"
        
        # 测试无效参数 - 年龄
        with pytest.raises(ConfigurationError):
            validate_function(name="John", age=-5)
        
        # 测试无效参数 - 名称
        with pytest.raises(ConfigurationError):
            validate_function(name="", age=30)
    
    def test_validate_arguments_decorator_with_exception(self, custom_error_handler):
        """测试参数验证装饰器 - 验证函数抛出异常"""
        # 创建会抛出异常的验证函数
        def failing_validator(x):
            if x > 10:
                raise ValueError("Value too large")
            return True
        
        # 创建测试函数
        @custom_error_handler.validate_arguments(value=failing_validator)
        def test_function(value):
            return f"Value: {value}"
        
        # 测试验证失败
        with pytest.raises(ConfigurationError):
            test_function(value=20)
    
    def test_get_error_handler_singleton(self):
        """测试获取错误处理器单例"""
        from app.llm.error_handler import get_error_handler
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        assert handler1 is handler2
    
    @mock.patch('time.sleep')
    def test_retry_on_llm_error_decorator(self, mock_sleep):
        """测试retry_on_llm_error装饰器"""
        # 创建测试函数
        @retry_on_llm_error(max_retries=2, base_delay=0.1)
        def decorated_function():
            decorated_function.attempts = getattr(decorated_function, 'attempts', 0) + 1
            if decorated_function.attempts < 2:
                raise GenerationError("Retry needed")
            return "Success"
        
        # 测试函数执行
        decorated_function.attempts = 0
        result = decorated_function()
        assert result == "Success"
        assert decorated_function.attempts == 2
    
    def test_safe_llm_call_decorator(self):
        """测试safe_llm_call装饰器"""
        # 创建测试函数
        @safe_llm_call(fallback_value="Safe fallback")
        def risky_function():
            raise Exception("Risky operation failed")
        
        # 测试异常被捕获
        result = risky_function()
        assert result == "Safe fallback"