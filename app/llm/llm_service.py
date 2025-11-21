"""大模型服务集成层

提供更高级别的大模型服务集成，简化使用并提供额外功能
"""

import logging
import asyncio
from typing import Any, Dict, Optional, Union, List
from concurrent.futures import ThreadPoolExecutor

from app.llm.llm_client import LLMClient
from app.llm.base import LLMResponse
from app.llm.exceptions import LLMError
from app.config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


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
                 max_workers: int = 5):
        """初始化大模型服务
        
        Args:
            config_manager: 配置管理器实例
            max_workers: 线程池最大工作线程数
        """
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._client = LLMClient(config_manager=config_manager)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._initialized = True
        
        logger.info("大模型服务初始化完成")
    
    def generate(self, 
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 **kwargs) -> LLMResponse:
        """生成文本响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 响应对象
        """
        try:
            logger.info(f"开始生成响应，模型: {self._client.get_config().get('model')}")
            response = self._client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                **kwargs
            )
            logger.info(f"生成响应成功，令牌使用: {response.tokens_used}")
            return response
        except Exception as e:
            logger.error(f"生成响应失败: {e}")
            raise
    
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
    
    def generate_batch(self, 
                      prompts: List[str],
                      system_prompt: Optional[str] = None,
                      **kwargs) -> List[LLMResponse]:
        """批量生成响应
        
        Args:
            prompts: 提示词列表
            system_prompt: 系统提示词
            **kwargs: 其他参数
            
        Returns:
            List[LLMResponse]: 响应对象列表
        """
        try:
            logger.info(f"开始批量生成响应，数量: {len(prompts)}")
            responses = self._client.generate_batch(
                prompts=prompts,
                system_prompt=system_prompt,
                **kwargs
            )
            
            # 统计成功和失败的数量
            success_count = sum(1 for r in responses if r.metadata.get('success') is not False)
            logger.info(f"批量生成完成，成功: {success_count}, 失败: {len(responses) - success_count}")
            
            return responses
        except Exception as e:
            logger.error(f"批量生成失败: {e}")
            raise
    
    async def async_generate(self, 
                            prompt: str,
                            system_prompt: Optional[str] = None,
                            **kwargs) -> LLMResponse:
        """异步生成响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 响应对象
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.generate(prompt, system_prompt, **kwargs)
        )
    
    async def async_generate_batch(self, 
                                  prompts: List[str],
                                  system_prompt: Optional[str] = None,
                                  **kwargs) -> List[LLMResponse]:
        """异步批量生成响应
        
        Args:
            prompts: 提示词列表
            system_prompt: 系统提示词
            **kwargs: 其他参数
            
        Returns:
            List[LLMResponse]: 响应对象列表
        """
        # 创建任务列表
        tasks = []
        for prompt in prompts:
            task = self.async_generate(prompt, system_prompt, **kwargs)
            tasks.append(task)
        
        # 等待所有任务完成
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def validate_template(self, template_name: str, **kwargs) -> bool:
        """验证模板和参数
        
        Args:
            template_name: 模板名称
            **kwargs: 模板变量
            
        Returns:
            bool: 验证是否通过
        """
        try:
            # 使用提示词管理器验证模板
            prompt_manager = self._client.get_prompt_manager()
            prompt_manager.format_prompt(template_name, **kwargs)
            return True
        except Exception as e:
            logger.error(f"模板验证失败: {e}")
            return False
    
    def get_available_templates(self) -> List[str]:
        """获取所有可用的提示词模板
        
        Returns:
            List[str]: 模板名称列表
        """
        try:
            prompt_manager = self._client.get_prompt_manager()
            return prompt_manager.list_prompts()
        except Exception as e:
            logger.error(f"获取模板列表失败: {e}")
            return []
    
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
            Dict[str, Any]: 健康状态信息
        """
        try:
            # 验证配置
            config_valid = self._client.validate_config()
            
            # 获取模型信息
            config = self._client.get_config()
            
            return {
                'status': 'healthy' if config_valid else 'unhealthy',
                'model': config.get('model', 'unknown'),
                'config_valid': config_valid,
                'available': config_valid
            }
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'available': False
            }
    
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