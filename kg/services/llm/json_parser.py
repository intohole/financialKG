"""
JSON解析器
用于从LLM响应中解析结构化JSON数据
"""

import json
from typing import Any, Dict, Optional

from langchain_core.output_parsers import BaseOutputParser


class JsonParser(BaseOutputParser[Dict[str, Any]]):
    """
    JSON解析器类
    从LLM响应中解析结构化JSON数据
    """

    def __init__(self):
        """
        初始化JSON解析器
        """
        pass

    def get_format_instructions(self) -> str:
        """
        获取JSON格式说明

        Returns:
            JSON格式说明字符串
        """
        return """
请严格按照JSON格式返回结果，不要包含任何解释性文本或额外内容。
JSON格式示例：
{{
    "key1": "value1",
    "key2": [
        {{"subkey": "subvalue"}},
        {{"subkey": "subvalue"}}
    ]
}}
"""

    def parse(self, text: str) -> Dict[str, Any]:
        """
        解析JSON字符串

        Args:
            text: 包含JSON的文本

        Returns:
            解析后的JSON对象
        """
        try:
            # 尝试直接解析
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            import re

            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # 尝试更宽松的提取
                lines = [line for line in text.strip().split("\n") if line.strip()]
                if lines[0].strip() == "{" and lines[-1].strip() == "}":
                    json_str = "\n".join(lines)
                    return json.loads(json_str)
                else:
                    raise ValueError(f"无法解析JSON: {text}")


# 全局JSON解析器实例
json_parser = JsonParser()
