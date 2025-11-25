"""
JSON提取器模块
提供使用LangChain的JsonOutputParser来提取和解析JSON的功能
专门用于与大模型交互的场景中稳健地提取JSON数据
"""

import json
import re
from typing import Dict, Any, Optional

from app.utils.logging_utils import get_logger

# 初始化日志记录器
logger = get_logger(__name__)

# LangChain导入 - 处理版本兼容性问题
try:
    from langchain.output_parsers import JsonOutputParser
    from langchain.schema import OutputParserException
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain_core.output_parsers import JsonOutputParser
        from langchain_core.exceptions import OutputParserException
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False


def extract_json_with_langchain(text: str) -> Optional[Dict[str, Any]]:
    """
    使用 LangChain 的 JsonOutputParser 来提取和解析 JSON。
    这是最稳健、最推荐的方法，尤其是在与大模型交互的场景中。
    
    Args:
        text: 可能包含 JSON 的文本字符串。

    Returns:
        解析后的 Python 字典，如果提取失败则返回 None。
    """
    if not LANGCHAIN_AVAILABLE:
        logger.warning("LangChain JsonOutputParser 不可用，使用备用方法")
        return extract_json_fallback(text)
    
    parser = JsonOutputParser()

    try:
        # LangChain 的 parser 会智能地寻找并解析 JSON
        return parser.parse(text)
    except OutputParserException as e:
        logger.error(f"JSON 解析失败: {e}")
        # e.llm_output 包含了原始的、未解析的输出，便于调试
        if hasattr(e, 'llm_output'):
            logger.debug(f"原始模型输出: {e.llm_output}")
        # 备用方案
        return extract_json_fallback(text)
    except Exception as e:
        logger.error(f"LangChain解析异常: {e}")
        return extract_json_fallback(text)


def extract_json_fallback(text: str) -> Optional[Dict[str, Any]]:
    """
    备用JSON提取方法
    当LangChain解析失败时，尝试手动提取JSON字符串
    
    Args:
        text: 可能包含 JSON 的文本字符串。
        
    Returns:
        解析后的 Python 字典，如果提取失败则返回 None。
    """
    import re
    
    # 尝试匹配 ```json 和 ``` 之间的内容
    json_pattern = r'```json\s*([\s\S]*?)\s*```'
    match = re.search(json_pattern, text)
    
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"手动JSON解析失败: {e}")
            return None
    
    # 尝试匹配 { 和 } 之间的内容
    brace_pattern = r'\{[\s\S]*\}'
    match = re.search(brace_pattern, text)
    
    if match:
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"大括号JSON解析失败: {e}")
            return None
    
    return None


def extract_json_robust(text: str) -> Optional[Dict[str, Any]]:
    """
    稳健的JSON提取方法
    结合LangChain解析和备用方法，提高成功率
    
    Args:
        text: 可能包含 JSON 的文本字符串。
        
    Returns:
        解析后的 Python 字典，如果提取失败则返回 None。
    """
    # 首先尝试LangChain方法
    result = extract_json_with_langchain(text)
    if result is not None:
        return result
    else:
        # LangChain失败时，尝试备用方法
        logger.warning("LangChain解析失败，尝试备用方法")
        return extract_json_fallback(text)