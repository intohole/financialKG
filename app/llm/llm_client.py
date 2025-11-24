"""大模型客户端

基于LangChain实现的大模型调用客户端，提供与多种大模型服务的交互功能
"""

import time
import logging
from typing import Any, Dict, Optional, Union, List
from contextlib import contextmanager

import langchain
from langchain_openai import ChatOpenAI
from langchain_core.messages import (SystemMessage, HumanMessage, AIMessage, 
                                     ChatMessage, BaseMessage)
# from langchain_core.callbacks import get_openai_callback  # 暂时移除，新版本API变更

from app.config.config_manager import ConfigManager, LLMConfig
from app.llm.base import BaseLLMService, LLMResponse
from app.llm.exceptions import (
    LLMError, GenerationError, ConfigurationError, 
    RateLimitError, AuthenticationError, ServiceUnavailableError
)
from app.llm.prompt_manager import PromptManager


logger = logging.getLogger(__name__)


class LLMClient(BaseLLMService):
    """基于LangChain的大模型客户端
    
    提供与大模型服务的交互功能，支持配置管理、响应生成、批处理等功能
    """
    
    def __init__(self, 
                 config_manager: Optional[ConfigManager] = None,
                 prompt_manager: Optional[PromptManager] = None,
                 **kwargs):
        """初始化大模型客户端
        
        Args:
            config_manager: 配置管理器实例
            prompt_manager: 提示词管理器实例
            **kwargs: 可选的配置覆盖项
        """
        self._config_manager = config_manager or ConfigManager()
        self._prompt_manager = prompt_manager or PromptManager()
        self._llm_config = None
        self._llm_instance = None
        self._custom_config = kwargs
        
        # 初始化配置和LLM实例
        self._initialize()
        
        # 添加配置变更监听
        self._config_manager.add_change_callback(self._on_config_change)
    
    def _initialize(self) -> None:
        """初始化客户端
        
        加载配置并创建LLM实例
        """
        try:
            # 获取配置
            self._llm_config = self._get_merged_config()
            
            # 验证配置
            if not self.validate_config():
                raise ConfigurationError("无效的LLM配置")
            
            # 创建LLM实例
            self._create_llm_instance()
            
            logger.info(f"大模型客户端初始化成功，模型: {self._llm_config.model}")
        except Exception as e:
            logger.error(f"大模型客户端初始化失败: {e}")
            raise
    
    def _get_merged_config(self) -> LLMConfig:
        """获取合并后的配置
        
        合并配置管理器中的配置和自定义配置
        
        Returns:
            LLMConfig: 合并后的配置对象
        """
        base_config = self._config_manager.get_llm_config()
        
        # 创建配置字典
        config_dict = {
            'model': base_config.model,
            'api_key': base_config.api_key,
            'base_url': base_config.base_url,
            'timeout': base_config.timeout,
            'max_retries': base_config.max_retries,
            'temperature': base_config.temperature,
            'max_tokens': base_config.max_tokens
        }
        
        # 使用自定义配置覆盖
        config_dict.update(self._custom_config)
        
        return LLMConfig(**config_dict)
    
    def _create_llm_instance(self) -> None:
        """创建LangChain LLM实例
        
        根据配置创建适当的LangChain LLM实例
        """
        config = self._llm_config
        
        try:
            # 检查必要的配置项
            if not config.api_key:
                raise ConfigurationError("缺少API密钥")
            
            # 创建ChatOpenAI实例（支持OpenAI兼容的API）
            self._llm_instance = ChatOpenAI(
                model_name=config.model,
                openai_api_key=config.api_key,
                openai_api_base=config.base_url or None,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                request_timeout=config.timeout,
                max_retries=config.max_retries
            )
            
            logger.debug(f"LangChain LLM实例创建成功")
        except Exception as e:
            logger.error(f"创建LLM实例失败: {e}")
            raise ConfigurationError(f"创建LLM实例失败: {e}")
    
    def _on_config_change(self) -> None:
        """配置变更回调
        
        当配置文件变更时重新初始化客户端
        """
        logger.info("检测到配置变更，重新初始化大模型客户端")
        try:
            self._initialize()
        except Exception as e:
            logger.error(f"配置变更后重新初始化失败: {e}")
    
    def validate_config(self) -> bool:
        """验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        config = self._llm_config
        
        # 检查必填项
        if not all([config.model, config.api_key]):
            logger.error("配置验证失败: 缺少必要的配置项")
            return False
        
        # 检查数值范围
        if not (0 <= config.temperature <= 2):
            logger.error(f"配置验证失败: temperature值 {config.temperature} 超出有效范围 [0, 2]")
            return False
        
        if config.max_tokens <= 0:
            logger.error(f"配置验证失败: max_tokens值 {config.max_tokens} 必须大于0")
            return False
        
        if config.timeout <= 0:
            logger.error(f"配置验证失败: timeout值 {config.timeout} 必须大于0")
            return False
        
        if config.max_retries < 0:
            logger.error(f"配置验证失败: max_retries值 {config.max_retries} 不能为负数")
            return False
        
        return True
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本响应
        
        Args:
            prompt: 提示文本
            **kwargs: 额外参数，包括：
                - system_prompt: 系统提示词
                - temperature: 温度参数（覆盖默认配置）
                - max_tokens: 最大令牌数（覆盖默认配置）
                - model: 模型名称（覆盖默认配置）
            
        Returns:
            LLMResponse: 包含生成内容和元数据的响应对象
        """
        start_time = time.time()
        attempt = 0
        max_retries = kwargs.get('max_retries', self._llm_config.max_retries)
        
        while attempt <= max_retries:
            attempt += 1
            
            try:
                # 构建消息列表
                messages = []
                
                # 添加系统提示词（如果提供）
                system_prompt = kwargs.get('system_prompt')
                if system_prompt:
                    messages.append(SystemMessage(content=system_prompt))
                
                # 添加用户提示词
                messages.append(HumanMessage(content=prompt))
                
                # 准备调用参数
                call_kwargs = {}
                if 'temperature' in kwargs:
                    call_kwargs['temperature'] = kwargs['temperature']
                if 'max_tokens' in kwargs:
                    call_kwargs['max_tokens'] = kwargs['max_tokens']
                if 'model' in kwargs:
                    call_kwargs['model'] = kwargs['model']
                
                # 生成响应
                response = self._llm_instance.invoke(messages, **call_kwargs)
                
                # 计算延迟
                latency = time.time() - start_time
                
                # 尝试从response对象中获取token信息
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
                cost = 0
                
                # 检查response对象是否有token使用信息
                if hasattr(response, 'usage'):
                    usage = response.usage
                    prompt_tokens = usage.get('prompt_tokens', 0)
                    completion_tokens = usage.get('completion_tokens', 0)
                    total_tokens = usage.get('total_tokens', 0)
                elif hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
                    token_usage = response.response_metadata['token_usage']
                    prompt_tokens = token_usage.get('prompt_tokens', 0)
                    completion_tokens = token_usage.get('completion_tokens', 0)
                    total_tokens = token_usage.get('total_tokens', 0)
                elif hasattr(response, 'metadata') and 'token_usage' in response.metadata:
                    token_usage = response.metadata['token_usage']
                    prompt_tokens = token_usage.get('prompt_tokens', 0)
                    completion_tokens = token_usage.get('completion_tokens', 0)
                    total_tokens = token_usage.get('total_tokens', 0)
                else:
                    # 如果没有token信息，使用简单的估算方法
                    # 注意：这个估算可能不准确，仅作为备选方案
                    import tiktoken
                    try:
                        # 使用tiktoken库估算token数量（如果可用）
                        encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4的编码方案
                        prompt_tokens = sum(len(encoding.encode(msg.content)) for msg in messages)
                        completion_tokens = len(encoding.encode(response.content))
                        total_tokens = prompt_tokens + completion_tokens
                    except Exception:
                        # 如果tiktoken不可用，使用字符数粗略估算（不太准确）
                        prompt_text = " ".join(msg.content for msg in messages)
                        prompt_tokens = len(prompt_text) // 4  # 粗略估算：4个字符约等于1个token
                        completion_tokens = len(response.content) // 4
                        total_tokens = prompt_tokens + completion_tokens
                
                # 粗略估算成本（基于常见的OpenAI定价，需要根据实际模型调整）
                # 这里使用简化的定价模型，实际项目中应该根据具体模型和服务提供商调整
                if self._llm_config.model and 'gpt-4' in self._llm_config.model.lower():
                    cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
                elif self._llm_config.model and 'gpt-3.5' in self._llm_config.model.lower():
                    cost = (prompt_tokens * 0.0015 + completion_tokens * 0.002) / 1000
                elif self._llm_config.model and 'glm-4' in self._llm_config.model.lower():
                    # GLM-4的近似定价
                    cost = (prompt_tokens * 0.01 + completion_tokens * 0.02) / 1000
                
                # 构建响应对象
                llm_response = LLMResponse(
                    content=response.content,
                    metadata={
                        'model': self._llm_config.model,
                        'attempt': attempt,
                        'timestamp': time.time()
                    },
                    cost=cost,
                    latency=latency,
                    tokens_used={
                        'prompt': prompt_tokens,
                        'completion': completion_tokens,
                        'total': total_tokens
                    }
                )
                
                logger.info(f"生成成功，模型: {self._llm_config.model}, 尝试次数: {attempt}, 延迟: {latency:.2f}s")
                return llm_response
                    
            except Exception as e:
                logger.error(f"生成失败 (尝试 {attempt}/{max_retries}): {e}")
                
                # 根据错误类型处理
                try:
                    from langchain.schema.output_parser import OutputParserException
                    if isinstance(e, OutputParserException):
                        raise GenerationError(f"输出解析失败: {e}", model=self._llm_config.model)
                except ImportError:
                    # 如果无法导入OutputParserException，使用字符串匹配
                    if 'OutputParserException' in str(type(e)):
                        raise GenerationError(f"输出解析失败: {e}", model=self._llm_config.model)
                
                if 'rate limit' in str(e).lower() or 'too many requests' in str(e).lower():
                    # 速率限制错误，尝试重试
                    retry_after = attempt * 2  # 指数退避
                    logger.warning(f"速率限制，{retry_after}秒后重试")
                    time.sleep(retry_after)
                    continue
                elif 'authentication' in str(e).lower() or 'invalid api key' in str(e).lower():
                    raise AuthenticationError(f"认证失败: {e}")
                elif 'service unavailable' in str(e).lower() or 'server error' in str(e).lower():
                    # 服务不可用，尝试重试
                    retry_after = attempt
                    logger.warning(f"服务不可用，{retry_after}秒后重试")
                    time.sleep(retry_after)
                    continue
                elif attempt >= max_retries:
                    # 达到最大重试次数
                    raise GenerationError(
                        f"生成失败，已达最大重试次数: {max_retries}",
                        model=self._llm_config.model,
                        attempt=attempt
                    )
                else:
                    # 其他错误，尝试重试
                    time.sleep(1)
    
    def generate_batch(self, prompts: list, **kwargs) -> list[LLMResponse]:
        """批量生成文本响应
        
        Args:
            prompts: 提示文本列表
            **kwargs: 额外参数（同generate方法）
            
        Returns:
            list[LLMResponse]: 响应对象列表
        """
        results = []
        
        # 可以根据需要实现真正的并行批处理
        # 目前使用串行处理以简化错误处理
        for i, prompt in enumerate(prompts):
            try:
                logger.info(f"处理批量请求 {i+1}/{len(prompts)}")
                result = self.generate(prompt, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"批量请求 {i+1} 失败: {e}")
                # 创建一个错误响应对象
                error_response = LLMResponse(
                    content="",
                    metadata={
                        'error': str(e),
                        'prompt_index': i,
                        'success': False
                    }
                )
                results.append(error_response)
        
        return results
    
    def generate_from_template(self, prompt_name: str, **kwargs) -> LLMResponse:
        """使用提示词模板生成响应
        
        Args:
            prompt_name: 提示词模板名称
            **kwargs: 模板变量和生成参数
            
        Returns:
            LLMResponse: 响应对象
        """
        # 提取生成参数
        generate_kwargs = {}
        template_kwargs = {}
        
        for key, value in kwargs.items():
            if key in ['system_prompt', 'temperature', 'max_tokens', 'model', 'max_retries']:
                generate_kwargs[key] = value
            else:
                template_kwargs[key] = value
        
        # 格式化提示词
        prompt = self._prompt_manager.format_prompt(prompt_name, **template_kwargs)
        
        # 生成响应
        return self.generate(prompt, **generate_kwargs)
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        if not self._llm_config:
            return {}
        
        return {
            'model': self._llm_config.model,
            'base_url': self._llm_config.base_url,
            'timeout': self._llm_config.timeout,
            'max_retries': self._llm_config.max_retries,
            'temperature': self._llm_config.temperature,
            'max_tokens': self._llm_config.max_tokens,
            # 不返回API密钥
            **self._custom_config
        }
    
    def update_config(self, **kwargs) -> None:
        """更新配置
        
        Args:
            **kwargs: 要更新的配置项
        """
        # 更新自定义配置
        self._custom_config.update(kwargs)
        
        # 重新初始化
        self._initialize()
    
    def get_prompt_manager(self) -> PromptManager:
        """获取提示词管理器实例
        
        Returns:
            PromptManager: 提示词管理器实例
        """
        return self._prompt_manager
    
    def get_config_manager(self) -> ConfigManager:
        """获取配置管理器实例
        
        Returns:
            ConfigManager: 配置管理器实例
        """
        return self._config_manager
    
    @contextmanager
    def temporary_config(self, **kwargs):
        """临时使用指定配置
        
        Args:
            **kwargs: 临时配置项
        """
        original_config = self._custom_config.copy()
        try:
            self.update_config(**kwargs)
            yield self
        finally:
            self._custom_config = original_config
            self._initialize()
    
    def __del__(self):
        """析构函数
        
        清理资源
        """
        try:
            if self._config_manager:
                self._config_manager.remove_change_callback(self._on_config_change)
        except Exception:
            pass