"""
嵌入向量工具模块

提供向量计算、验证和处理的通用功能
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
from numpy.linalg import norm

logger = logging.getLogger(__name__)


def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量之间的余弦相似度

    Args:
        vec1: 第一个向量
        vec2: 第二个向量

    Returns:
        float: 余弦相似度，范围[-1, 1]

    Raises:
        ValueError: 当输入向量无效时
        ZeroDivisionError: 当向量范数为0时
    """
    try:
        if not vec1 or not vec2:
            raise ValueError("输入向量不能为空")

        if len(vec1) != len(vec2):
            raise ValueError(f"向量维度不匹配: {len(vec1)} != {len(vec2)}")

        vec1_np = np.array(vec1, dtype=np.float64)
        vec2_np = np.array(vec2, dtype=np.float64)

        # 计算余弦相似度
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = norm(vec1_np)
        norm2 = norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            raise ZeroDivisionError("向量范数为0，无法计算相似度")

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    except (ValueError, ZeroDivisionError) as e:
        logger.error(f"计算余弦相似度失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"计算余弦相似度时发生未知错误: {str(e)}")
        raise RuntimeError(f"计算余弦相似度失败: {str(e)}")


def validate_embedding(
    embedding: List[float], expected_dimension: Optional[int] = None
) -> bool:
    """
    验证嵌入向量的有效性

    Args:
        embedding: 要验证的嵌入向量
        expected_dimension: 期望的向量维度（可选）

    Returns:
        bool: 向量是否有效
    """
    try:
        # 检查是否为列表
        if not isinstance(embedding, list):
            return False

        # 检查是否为空
        if len(embedding) == 0:
            return False

        # 检查维度
        if expected_dimension is not None and len(embedding) != expected_dimension:
            return False

        # 检查所有元素是否为数字
        for value in embedding:
            if not isinstance(value, (int, float)):
                return False

        # 检查是否包含NaN或Infinity
        if any(not np.isfinite(x) for x in embedding):
            return False

        return True

    except Exception as e:
        logger.error(f"验证嵌入向量时发生错误: {str(e)}")
        return False


def normalize_embedding(embedding: List[float]) -> List[float]:
    """
    归一化嵌入向量

    Args:
        embedding: 要归一化的嵌入向量

    Returns:
        List[float]: 归一化后的向量

    Raises:
        ValueError: 当输入向量无效时
        ZeroDivisionError: 当向量范数为0时
    """
    try:
        if not validate_embedding(embedding):
            raise ValueError("无效的嵌入向量")

        embedding_np = np.array(embedding, dtype=np.float64)
        norm_value = norm(embedding_np)

        if norm_value == 0:
            raise ZeroDivisionError("向量范数为0，无法归一化")

        normalized = embedding_np / norm_value
        return normalized.tolist()

    except (ValueError, ZeroDivisionError) as e:
        logger.error(f"归一化嵌入向量失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"归一化嵌入向量时发生未知错误: {str(e)}")
        raise RuntimeError(f"归一化嵌入向量失败: {str(e)}")


def aggregate_embeddings(
    embeddings: List[List[float]], method: str = "mean"
) -> List[float]:
    """
    聚合多个嵌入向量

    Args:
        embeddings: 嵌入向量列表
        method: 聚合方法 (mean, sum, max, min)

    Returns:
        List[float]: 聚合后的向量

    Raises:
        ValueError: 当输入无效时
    """
    try:
        if not embeddings:
            raise ValueError("嵌入向量列表不能为空")

        # 验证所有向量
        for embedding in embeddings:
            if not validate_embedding(embedding):
                raise ValueError("发现无效的嵌入向量")

        # 检查所有向量维度是否一致
        dimension = len(embeddings[0])
        if any(len(emb) != dimension for emb in embeddings):
            raise ValueError("所有嵌入向量的维度必须一致")

        embeddings_np = np.array(embeddings, dtype=np.float64)

        if method == "mean":
            result = np.mean(embeddings_np, axis=0)
        elif method == "sum":
            result = np.sum(embeddings_np, axis=0)
        elif method == "max":
            result = np.max(embeddings_np, axis=0)
        elif method == "min":
            result = np.min(embeddings_np, axis=0)
        else:
            raise ValueError(f"不支持的聚合方法: {method}")

        return result.tolist()

    except ValueError as e:
        logger.error(f"聚合嵌入向量失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"聚合嵌入向量时发生未知错误: {str(e)}")
        raise RuntimeError(f"聚合嵌入向量失败: {str(e)}")


def batch_normalize_embeddings(embeddings: List[List[float]]) -> List[List[float]]:
    """
    批量归一化嵌入向量

    Args:
        embeddings: 嵌入向量列表

    Returns:
        List[List[float]]: 归一化后的嵌入向量列表
    """
    try:
        return [normalize_embedding(emb) for emb in embeddings]
    except Exception as e:
        logger.error(f"批量归一化嵌入向量失败: {str(e)}")
        raise
