"""
文本处理工具模块

提供文本清洗、规范化、分割等通用功能
"""
import logging
import re
from typing import List, Dict, Any, Optional, Set
import string

logger = logging.getLogger(__name__)


def clean_text(text: str, remove_punctuation: bool = False) -> str:
    """
    清洗文本
    
    Args:
        text: 要清洗的文本
        remove_punctuation: 是否移除标点符号
        
    Returns:
        str: 清洗后的文本
    """
    try:
        if not isinstance(text, str):
            raise TypeError("输入必须是字符串")
        
        # 去除多余空白字符
        cleaned = ' '.join(text.split())
        
        # 去除首尾空白
        cleaned = cleaned.strip()
        
        # 移除标点符号（如果需要）
        if remove_punctuation:
            # 创建一个移除所有标点符号的映射表
            translator = str.maketrans('', '', string.punctuation)
            cleaned = cleaned.translate(translator)
        
        return cleaned
    
    except TypeError as e:
        logger.error(f"清洗文本失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"清洗文本时发生未知错误: {str(e)}")
        raise RuntimeError(f"清洗文本失败: {str(e)}")


def split_text_into_chunks(text: str, max_chunk_size: int = 512, overlap: int = 0) -> List[str]:
    """
    将长文本分割成多个块
    
    Args:
        text: 要分割的文本
        max_chunk_size: 每个块的最大字符数
        overlap: 块之间的重叠字符数
        
    Returns:
        List[str]: 文本块列表
    """
    try:
        if not isinstance(text, str):
            raise TypeError("输入必须是字符串")
        
        if max_chunk_size <= 0:
            raise ValueError("最大块大小必须为正数")
        
        if overlap < 0 or overlap >= max_chunk_size:
            raise ValueError("重叠大小必须在0到max_chunk_size之间")
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + max_chunk_size, text_length)
            chunks.append(text[start:end])
            
            # 如果已经到达文本末尾，跳出循环
            if end == text_length:
                break
            
            # 更新起始位置，考虑重叠
            start = end - overlap
        
        return chunks
    
    except (TypeError, ValueError) as e:
        logger.error(f"分割文本失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"分割文本时发生未知错误: {str(e)}")
        raise RuntimeError(f"分割文本失败: {str(e)}")


def extract_keywords_from_text(text: str, max_keywords: int = 10) -> List[str]:
    """
    从文本中提取关键词（简单实现）
    
    Args:
        text: 要提取关键词的文本
        max_keywords: 返回的最大关键词数量
        
    Returns:
        List[str]: 关键词列表
    """
    try:
        if not isinstance(text, str):
            raise TypeError("输入必须是字符串")
        
        # 清洗文本
        cleaned = clean_text(text, remove_punctuation=True)
        
        # 转为小写
        cleaned = cleaned.lower()
        
        # 常见停用词列表
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'if', 'because', 'as',
            'what', 'when', 'where', 'how', 'who', 'which', 'this', 'that',
            'these', 'those', 'then', 'just', 'so', 'than', 'such', 'both',
            'through', 'about', 'for', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'shall', 'can', 'cannot', 'able', 'one', 'two', 'three',
            'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
            'hundred', 'thousand', 'million', 'billion', 'trillion'
        }
        
        # 分割文本为单词
        words = re.findall(r'\b\w+\b', cleaned)
        
        # 过滤停用词和短词
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # 统计词频
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按词频排序并返回前N个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        
        return keywords
    
    except TypeError as e:
        logger.error(f"提取关键词失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"提取关键词时发生未知错误: {str(e)}")
        raise RuntimeError(f"提取关键词失败: {str(e)}")


def normalize_text(text: str, lowercase: bool = True, remove_whitespace: bool = True) -> str:
    """
    规范化文本
    
    Args:
        text: 要规范化的文本
        lowercase: 是否转为小写
        remove_whitespace: 是否移除多余空白
        
    Returns:
        str: 规范化后的文本
    """
    try:
        if not isinstance(text, str):
            raise TypeError("输入必须是字符串")
        
        result = text
        
        if lowercase:
            result = result.lower()
        
        if remove_whitespace:
            result = ' '.join(result.split())
        
        return result
    
    except TypeError as e:
        logger.error(f"规范化文本失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"规范化文本时发生未知错误: {str(e)}")
        raise RuntimeError(f"规范化文本失败: {str(e)}")


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 要截断的文本
        max_length: 最大长度
        suffix: 截断后的后缀
        
    Returns:
        str: 截断后的文本
    """
    try:
        if not isinstance(text, str):
            raise TypeError("输入必须是字符串")
        
        if max_length <= 0:
            raise ValueError("最大长度必须为正数")
        
        if len(text) <= max_length:
            return text
        
        # 确保后缀不会导致文本过短
        suffix_length = len(suffix)
        truncate_at = max_length - suffix_length
        
        # 如果没有足够空间容纳后缀，直接返回空字符串加后缀
        if truncate_at <= 0:
            return suffix[:max_length]
        
        # 尝试在单词边界处截断
        if truncate_at < len(text) and text[truncate_at] != ' ':
            # 向前查找最近的空格
            while truncate_at > 0 and text[truncate_at] != ' ':
                truncate_at -= 1
            
            # 如果找不到空格，直接截断
            if truncate_at == 0:
                truncate_at = max_length - suffix_length
        
        return text[:truncate_at] + suffix
    
    except (TypeError, ValueError) as e:
        logger.error(f"截断文本失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"截断文本时发生未知错误: {str(e)}")
        raise RuntimeError(f"截断文本失败: {str(e)}")


def validate_text_input(text: str, min_length: int = 1, max_length: Optional[int] = None) -> bool:
    """
    验证文本输入
    
    Args:
        text: 要验证的文本
        min_length: 最小长度要求
        max_length: 最大长度要求（可选）
        
    Returns:
        bool: 文本是否有效
    """
    try:
        # 检查是否为字符串
        if not isinstance(text, str):
            return False
        
        # 检查最小长度
        if len(text.strip()) < min_length:
            return False
        
        # 检查最大长度
        if max_length is not None and len(text) > max_length:
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"验证文本输入时发生错误: {str(e)}")
        return False


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 0) -> List[str]:
    """
    将长文本分割成多个块（split_text_into_chunks的别名）
    
    Args:
        text: 要分割的文本
        chunk_size: 每个块的最大字符数
        overlap: 块之间的重叠字符数
        
    Returns:
        List[str]: 文本块列表
    """
    return split_text_into_chunks(text, max_chunk_size=chunk_size, overlap=overlap)
