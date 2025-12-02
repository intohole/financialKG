"""大模型服务基础接口

定义所有大模型服务实现必须遵循的接口规范
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass

# 添加异步支持的导入
import asyncio


@dataclass
class LLMResponse:
    """大模型响应数据类"""
    content: str
    metadata: Optional[Dict[str, Any]] = None
    cost: Optional[float] = None
    latency: Optional[float] = None
    tokens_used: Optional[Dict[str, int]] = None


class BaseLLMService(ABC):
    """大模型服务基础抽象类
    
    定义大模型服务的标准接口，所有具体实现必须遵循此接口
    """
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本响应
        
        Args:
            prompt: 提示文本
            **kwargs: 额外参数
            
        Returns:
            LLMResponse: 包含生成内容和元数据的响应对象
        """
        pass
    
    @abstractmethod
    def generate_batch(self, prompts: list, **kwargs) -> list[LLMResponse]:
        """批量生成文本响应
        
        Args:
            prompts: 提示文本列表
            **kwargs: 额外参数
            
        Returns:
            list[LLMResponse]: 响应对象列表
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证服务配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """获取当前服务配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        pass
    
    @abstractmethod
    def update_config(self, **kwargs) -> None:
        """更新服务配置
        
        Args:
            **kwargs: 要更新的配置项
        """
        pass
    
    # 以下是异步方法声明
    @abstractmethod
    async def generate_async(self, prompt: str, **kwargs) -> LLMResponse:
        """异步生成文本响应
        
        Args:
            prompt: 提示文本
            **kwargs: 额外参数
            
        Returns:
            LLMResponse: 包含生成内容和元数据的响应对象
        """
        pass
    
    @abstractmethod
    async def generate_batch_async(self, prompts: list, **kwargs) -> list[LLMResponse]:
        """异步批量生成文本响应
        
        Args:
            prompts: 提示文本列表
            **kwargs: 额外参数
            
        Returns:
            list[LLMResponse]: 响应对象列表
        """
        pass
