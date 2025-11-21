"""
基础服务类 - 提供大模型调用和响应处理的核心功能
"""
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from app.config.config_manager import ConfigManager
from app.llm.prompt_manager import PromptManager
from app.llm.llm_service import LLMService

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    基础服务类，提供大模型调用和响应处理的核心功能
    
    功能：
    - 大模型调用封装
    - JSON响应提取
    - 响应数据验证
    - 错误处理和日志记录
    
    使用方式：
    1. 继承此类并实现parse_llm_response方法
    2. 使用generate_with_prompt方法调用大模型
    3. 使用提供的工具方法处理响应
    """
    
    def __init__(self):
        """初始化基础服务"""
        self.config = ConfigManager()
        self.prompt_manager = PromptManager()
        self.llm_service = LLMService()
        logger.info(f"初始化 {self.__class__.__name__}")
    
    async def generate_with_prompt(self, prompt_key: str, **kwargs) -> str:
        """
        使用指定的prompt调用大模型
        
        Args:
            prompt_key: prompt的键名
            **kwargs: prompt参数
            
        Returns:
            大模型响应文本
            
        Raises:
            ValueError: 当prompt不存在时
            RuntimeError: 当LLM调用失败时
        """
        try:
            # 获取prompt模板
            prompt_template = self.prompt_manager.get_prompt(prompt_key)
            if not prompt_template:
                raise ValueError(f"Prompt不存在: {prompt_key}")
            
            # 格式化prompt
            formatted_prompt = prompt_template.format(**kwargs)
            logger.debug(f"格式化后的prompt预览: {formatted_prompt[:200]}...")
            
            # 调用大模型
            logger.info(f"开始LLM调用: {prompt_key}")
            response_obj = await self.llm_service.async_generate(formatted_prompt)
            response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
            
            if not response:
                raise RuntimeError("LLM返回空响应")
            
            logger.info(f"LLM调用成功: {prompt_key}, 响应长度: {len(response)}")
            return response
            
        except ValueError as e:
            logger.error(f"参数错误: {e}")
            raise
        except Exception as e:
            logger.error(f"LLM调用失败: {prompt_key} - {str(e)}")
            raise RuntimeError(f"LLM调用失败: {str(e)}")
    
    def extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        从响应文本中提取JSON对象
        
        Args:
            response: 大模型响应文本
            
        Returns:
            提取的JSON对象，如果提取失败返回None
            
        提取策略：
        1. 查找```json代码块
        2. 查找{}包围的JSON对象
        3. 返回第一个有效的JSON对象
        """
        if not response:
            return None
        
        # 尝试提取代码块中的JSON
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, response, re.IGNORECASE)
        
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
        
        # 尝试直接提取JSON对象
        json_pattern = r'\{[\s\S]*?\}'
        matches = re.findall(json_pattern, response)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        logger.warning("未能从响应中提取有效的JSON")
        return None
    
    def extract_json_array_from_response(self, response: str) -> Optional[List[Dict[str, Any]]]:
        """
        从响应文本中提取JSON数组
        
        Args:
            response: 大模型响应文本
            
        Returns:
            提取的JSON数组，如果提取失败返回None
        """
        if not response:
            return None
        
        # 尝试提取代码块中的JSON数组
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, response, re.IGNORECASE)
        
        for match in matches:
            try:
                parsed = json.loads(match.strip())
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                continue
        
        # 尝试直接提取JSON数组
        json_pattern = r'\[[\s\S]*?\]'
        matches = re.findall(json_pattern, response)
        
        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                continue
        
        logger.warning("未能从响应中提取有效的JSON数组")
        return None
    
    def validate_response_data(self, data: Any, required_fields: List[str]) -> bool:
        """
        验证响应数据是否包含必需的字段
        
        Args:
            data: 要验证的数据（通常是字典）
            required_fields: 必需的字段列表
            
        Returns:
            如果所有必需字段都存在返回True，否则返回False
        """
        if not isinstance(data, dict):
            logger.error(f"响应数据不是字典类型: {type(data)}")
            return False
        
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"响应数据缺少必需字段: {missing_fields}")
            return False
        
        return True
    
    @abstractmethod
    async def parse_llm_response(self, response: str) -> Any:
        """
        解析LLM响应，子类必须实现此方法
        
        Args:
            response: 大模型原始响应文本
            
        Returns:
            解析后的结构化数据
            
        Note:
            每个服务类需要实现自己的响应解析逻辑
        """
        pass