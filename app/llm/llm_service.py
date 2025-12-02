"""大模型服务集成层

提供更高级别的大模型服务集成，简化使用并提供额外功能
"""

import asyncio
from typing import Any, Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor

from app.llm.llm_client import LLMClient
from app.llm.base import LLMResponse
from app.config.config_manager import ConfigManager
from app.utils.logging_utils import get_logger


logger = get_logger(__name__)


class LLMService:
    """大模型服务集成类
    
    提供更高级别的API，简化大模型调用的使用，支持异步操作
    """
    
    _instance = None
    _lock = asyncio.Lock() if hasattr(asyncio, 'Lock') else None
    
    def __new__(cls, *args, **kwargs):
        """单例模式
        
        确保全局只有一个LLMService实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 config_manager: Optional[ConfigManager] = None,
                 max_workers: int = 5,
                 executor: Optional[ThreadPoolExecutor] = None):
        """初始化大模型服务
        
        Args:
            config_manager: 配置管理器实例
            max_workers: 线程池最大工作线程数
            executor: 自定义线程池执行器（可选）
        """
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._client = LLMClient(config_manager=config_manager)
        # 使用自定义执行器或创建新的
        self._executor = executor if executor else ThreadPoolExecutor(max_workers=max_workers)
        self._initialized = True
        self._call_history = []  # 用于统计和历史记录
        
        logger.info("大模型服务初始化完成")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        """生成响应（符合基类接口）
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 响应对象
        """
        # 直接调用客户端的generate方法
        response = self._client.generate(prompt, **kwargs)
        return response
    
    def generate_from_template(self, 
                              template_name: str,
                              system_prompt: Optional[str] = None,
                              **kwargs) -> LLMResponse:
        """使用模板生成响应
        
        Args:
            template_name: 模板名称
            system_prompt: 系统提示词
            **kwargs: 模板变量和其他参数
            
        Returns:
            LLMResponse: 响应对象
        """
        try:
            logger.info(f"使用模板生成响应: {template_name}")
            response = self._client.generate_from_template(
                prompt_name=template_name,
                system_prompt=system_prompt,
                **kwargs
            )
            logger.info(f"模板生成成功，令牌使用: {response.tokens_used}")
            return response
        except Exception as e:
            logger.error(f"模板生成失败: {e}")
            raise
    
    def generate_batch(self, prompts: List[str], system_prompt: Optional[str] = None, **kwargs) -> list[LLMResponse]:
        """批量生成响应（符合基类接口）
        
        Args:
            prompts: 提示词列表
            system_prompt: 系统提示词
            **kwargs: 其他参数
            
        Returns:
            list[LLMResponse]: 响应对象列表
        """
        # 直接调用客户端的generate_batch方法
        return self._client.generate_batch(prompts, **kwargs)
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本并返回纯文本内容
        
        Args:
            prompt: 提示文本
            **kwargs: 额外参数
            
        Returns:
            str: 生成的文本内容
        """
        try:
            response = await self._client.generate_async(prompt, **kwargs)
            self._update_call_history(prompt, response, **kwargs)
            return response.content
        except Exception as e:
            logger.error(f"生成文本失败: {e}")
            self._update_call_history(prompt, None, error=str(e), **kwargs)
            raise
    
    async def generate_text_with_template(self, template_name: str, **kwargs) -> str:
        """使用提示词模板生成文本
        
        Args:
            template_name: 模板名称
            **kwargs: 模板参数
            
        Returns:
            str: 生成的文本内容
        """
        try:
            # 尝试从客户端获取prompt_manager
            prompt_manager = self._client.get_prompt_manager()
            if hasattr(prompt_manager, 'format_prompt'):
                prompt = prompt_manager.format_prompt(template_name, **kwargs)
            else:
                # 回退方案
                raise Exception(f"PromptManager没有format_prompt方法")
            
            response = await self._client.generate_async(prompt, **kwargs)
            self._update_call_history(prompt, response, template=template_name, **kwargs)
            return response.content
        except Exception as e:
            logger.error(f"使用模板生成文本失败: {e}")
            self._update_call_history(None, None, template=template_name, error=str(e), **kwargs)
            raise
    
    async def generate_async(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        """异步生成响应（符合基类接口）
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 响应对象
        """
        # 直接调用客户端的generate_async方法
        response = await self._client.generate_async(prompt, **kwargs)
        return response
    
    async def generate_batch_async(self, prompts: List[str], system_prompt: Optional[str] = None, **kwargs) -> list[LLMResponse]:
        """异步批量生成响应（符合基类接口）
        
        Args:
            prompts: 提示词列表
            system_prompt: 系统提示词
            **kwargs: 其他参数
            
        Returns:
            list[LLMResponse]: 响应对象列表
        """
        # 直接调用客户端的generate_batch_async方法
        responses = await self._client.generate_batch_async(prompts, **kwargs)
        return responses
    
    # 保持向后兼容的异步方法
    async def generate_text_async(self, prompt: str, **kwargs) -> str:
        """异步生成文本内容（向后兼容测试）
        
        Args:
            prompt: 用户提示词
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本内容
        """
        response = await self.generate_async(prompt, **kwargs)
        return response.content
    
    async def generate_batch_text_async(self, prompts: List[str], **kwargs) -> List[str]:
        """异步批量生成文本内容
        
        Args:
            prompts: 提示词列表
            **kwargs: 其他参数
            
        Returns:
            List[str]: 生成的文本内容列表
        """
        responses = await self.generate_batch_async(prompts, **kwargs)
        return [r.content if isinstance(r, LLMResponse) else str(r) for r in responses]
    
    def validate_template(self, template_name: str, **kwargs) -> Dict[str, Any]:
        """验证模板和参数
        
        Args:
            template_name: 模板名称
            **kwargs: 模板变量
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        # 直接调用客户端的validate_template方法
        return self._client.validate_template(template_name, **kwargs)
    
    def get_available_templates(self) -> List[str]:
        """获取所有可用的提示词模板
        
        Returns:
            List[str]: 模板名称列表
        """
        # 直接调用客户端的get_all_prompts方法
        return self._client.get_all_prompts()
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        try:
            return self._client.get_config()
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            return {}
    
    def update_config(self, **kwargs) -> None:
        """更新配置
        
        Args:
            **kwargs: 配置项
        """
        try:
            logger.info(f"更新大模型配置: {kwargs}")
            self._client.update_config(**kwargs)
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 健康状态
        """
        return self._client.health_check()
    
    def _update_call_history(self, prompt=None, response=None, template=None, error=None, **kwargs) -> None:
        """更新调用历史记录
        
        Args:
            prompt: 提示词
            response: 响应对象
            template: 模板名称
            error: 错误信息
            **kwargs: 其他参数
        """
        import time
        # 提取必要信息用于历史记录
        model = kwargs.get('model', 'unknown')
        tokens = response.tokens_used if response and hasattr(response, 'tokens_used') else 0
        success = error is None
        
        self._call_history.append({
            'timestamp': time.time(),
            'model': model,
            'tokens': tokens,
            'success': success,
            'template': template
        })
        
        # 限制历史记录长度
        if len(self._call_history) > 1000:
            self._call_history = self._call_history[-1000:]
    
    def _extract_variables_from_template(self, template: str) -> List[str]:
        """从模板中提取变量名
        
        Args:
            template: 模板字符串
            
        Returns:
            List[str]: 变量名列表
        """
        import re
        # 匹配 {variable} 格式的变量
        matches = re.findall(r'\{(\w+)\}', template)
        # 去重
        return list(set(matches))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 包含调用次数、成功率、令牌使用等统计信息
        """
        if not self._call_history:
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_tokens': 0,
                'success_rate': 0
            }
        
        total_calls = len(self._call_history)
        successful_calls = sum(1 for call in self._call_history if call['success'])
        failed_calls = total_calls - successful_calls
        total_tokens = sum(call['tokens'] for call in self._call_history)
        
        return {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'total_tokens': total_tokens,
            'success_rate': (successful_calls / total_calls * 100) if total_calls > 0 else 0
        }
    
    def clear_stats(self) -> None:
        """清除统计信息和调用历史"""
        self._call_history = []
    
    def close(self) -> None:
        """关闭服务
        
        释放资源
        """
        try:
            if hasattr(self, '_executor'):
                self._executor.shutdown(wait=True)
                logger.info("大模型服务已关闭")
        except Exception as e:
            logger.error(f"关闭服务时出错: {e}")
    
    def __enter__(self):
        """上下文管理器入口
        
        Returns:
            LLMService: 服务实例
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪
        """
        self.close()
    
    @classmethod
    async def get_instance(cls) -> 'LLMService':
        """异步获取单例实例
        
        Returns:
            LLMService: 服务实例
        """
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance


# 创建默认实例
llm_service = LLMService()


def get_llm_service() -> LLMService:
    """获取大模型服务实例
    
    Returns:
        LLMService: 服务实例
    """
    return llm_service