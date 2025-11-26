"""
Embedding 数据模型
定义嵌入服务的请求和响应数据结构
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class EmbeddingRequest:
    """
    嵌入请求数据模型
    """
    texts: List[str]  # 要嵌入的文本列表
    model: Optional[str] = None  # 指定模型（可选）
    use_cache: bool = True  # 是否使用缓存
    parameters: Optional[Dict[str, Any]] = None  # 额外参数


@dataclass
class EmbeddingResponse:
    """
    嵌入响应数据模型
    """
    embeddings: List[List[float]]  # 嵌入向量列表
    model: str  # 使用的模型
    total_tokens: Optional[int] = None  # 总令牌数（如果可用）
    cost: Optional[float] = None  # 成本估算（如果可用）
    processing_time: Optional[float] = None  # 处理时间（秒）
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据


@dataclass
class EmbeddingResult:
    """
    单个文本嵌入结果
    """
    text: str  # 原始文本
    embedding: List[float]  # 嵌入向量
    index: int  # 在原始请求中的索引
    tokens_used: Optional[int] = None  # 使用的令牌数


@dataclass
class EmbeddingStats:
    """
    嵌入服务统计信息
    """
    total_embeddings: int  # 总嵌入次数
    cached_embeddings: int  # 缓存命中次数
    unique_texts: int  # 唯一文本数
    avg_processing_time: float  # 平均处理时间
    total_tokens: int  # 总令牌数
    total_cost: float  # 总成本估算
