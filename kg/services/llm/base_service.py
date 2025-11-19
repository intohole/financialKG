"""大模型基础服务类
提供通用的OpenAI API调用接口
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from openai import OpenAI

from kg.core.config import llm_config


class BaseLLMService(ABC):
    """大模型基础服务类"""

    def __init__(self):
        """初始化大模型服务"""
        self.client = llm_config.get_client()
        self.model = llm_config.model
        self.temperature = llm_config.temperature
        self.max_tokens = llm_config.max_tokens

    def get_client(self):
        """获取LLM客户端"""
        return self.client

    def generate_response(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """生成LLM响应"""
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            params.update(kwargs)

            response = self.client.chat.completions.create(**params)
            normalized_response = normalize_openai_response(response)
            return normalized_response
        except Exception as e:
            raise RuntimeError(f"调用大模型API失败: {e}")

    @abstractmethod
    def extract_structured_data(
        self, prompt: str, schema: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """提取结构化数据"""
        pass

    def _create_system_prompt(self, prompt_template: str, **kwargs) -> str:
        """
        创建系统提示词

        Args:
            prompt_template: 提示词模板
            **kwargs: 模板参数

        Returns:
            格式化后的系统提示词
        """
        return prompt_template.format(**kwargs)

    def _create_user_prompt(self, text: str, prompt_template: str, **kwargs) -> str:
        """
        创建用户提示词

        Args:
            text: 输入文本
            prompt_template: 提示词模板
            **kwargs: 模板参数

        Returns:
            格式化后的用户提示词
        """
        return prompt_template.format(text=text, **kwargs)

    def _call_api(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        调用OpenAI API

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            response_format: 响应格式，用于结构化输出

        Returns:
            API响应结果
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if response_format:
            params["response_format"] = response_format

        try:
            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content

            # 尝试解析JSON响应
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 如果不是JSON格式，返回原始文本
                return {"result": content}

        except Exception as e:
            raise RuntimeError(f"调用大模型API失败: {e}")

    def extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        从响应文本中提取JSON

        Args:
            response_text: 响应文本

        Returns:
            解析后的JSON对象
        """
        # 尝试直接解析
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # 尝试从文本中提取JSON部分
        import re

        json_pattern = r"```json\s*(.*?)\s*```"
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试查找JSON对象
        json_pattern = r"\{.*\}"
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        # 如果无法解析，返回原始文本
        return {"result": response_text}


def normalize_openai_response(response: Any) -> Dict[str, Any]:
    """
    标准化OpenAI API响应格式

    Args:
        response: OpenAI API原始响应

    Returns:
        标准化后的响应字典
    """
    if hasattr(response, "choices") and response.choices:
        choice = response.choices[0]
        return {
            "id": response.id,
            "model": response.model,
            "created": response.created,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "content": choice.message.content,
            "finish_reason": choice.finish_reason,
        }
    return {}
