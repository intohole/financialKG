"""
去重服务接口模块

定义实体和关系去重的标准接口，支持通过配置自动化运行，用户无需关注具体实现逻辑
"""
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
from .base_service import AsyncService


class DeduplicationConfig:
    """
    去重配置类，用于控制去重行为
    
    提供统一的配置接口，使用户可以通过配置控制去重过程的各个方面，
    而无需了解底层实现细节
    """
    def __init__(self,
                 similarity_threshold: float = 0.85,
                 batch_size: int = 100,
                 limit: Optional[int] = None,
                 entity_types: Optional[List[str]] = None,
                 keyword: Optional[str] = None,
                 auto_merge: bool = True,
                 use_vector_search: bool = True,
                 fallback_to_string_similarity: bool = True,
                 min_entities_for_duplication: int = 2):
        """
        初始化去重配置
        
        Args:
            similarity_threshold: 相似度阈值，决定两个项目被认为是重复的标准
            batch_size: 批处理大小，用于控制一次处理的实体数量
            limit: 处理的实体数量限制
            entity_types: 要处理的实体类型列表，None表示处理所有类型
            keyword: 搜索关键词，用于基于关键词进行实体去重
            auto_merge: 是否自动合并重复项
            use_vector_search: 是否使用向量搜索加速去重过程
            fallback_to_string_similarity: 当向量搜索不可用时，是否回退到字符串相似度
            min_entities_for_duplication: 进行去重的最小实体数量
        """
        self.similarity_threshold = similarity_threshold
        self.batch_size = batch_size
        self.limit = limit
        self.entity_types = entity_types
        self.keyword = keyword
        self.auto_merge = auto_merge
        self.use_vector_search = use_vector_search
        self.fallback_to_string_similarity = fallback_to_string_similarity
        self.min_entities_for_duplication = min_entities_for_duplication


class DeduplicationResult:
    """
    去重结果类，统一封装去重操作的结果
    """
    def __init__(self,
                 success: bool,
                 total_processed: int,
                 total_duplicate_groups: int,
                 total_duplicates_merged: int,
                 message: str = "",
                 details: Optional[Dict[str, Any]] = None):
        """
        初始化去重结果
        
        Args:
            success: 去重操作是否成功
            total_processed: 处理的实体/关系总数
            total_duplicate_groups: 发现的重复组数量
            total_duplicates_merged: 合并的重复项数量
            message: 结果消息
            details: 结果详情字典
        """
        self.success = success
        self.total_processed = total_processed
        self.total_duplicate_groups = total_duplicate_groups
        self.total_duplicates_merged = total_duplicates_merged
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将结果转换为字典格式
        
        Returns:
            Dict[str, Any]: 包含结果信息的字典
        """
        return {
            "success": self.success,
            "total_processed": self.total_processed,
            "total_duplicate_groups": self.total_duplicate_groups,
            "total_duplicates_merged": self.total_duplicates_merged,
            "message": self.message,
            "details": self.details
        }


class DeduplicationServiceInterface(AsyncService):
    """
    去重服务接口
    
    提供简化的单一核心接口，支持通过配置自动化运行，用户无需关注具体实现逻辑
    """
    
    @abstractmethod
    async def deduplicate(self, config: DeduplicationConfig) -> DeduplicationResult:
        """
        执行自动化去重操作
        
        根据配置自动处理实体或关系的去重，支持按类型、关键词等多种过滤方式，
        并根据配置自动执行合并操作
        
        Args:
            config: 去重配置，控制去重行为
            
        Returns:
            DeduplicationResult: 去重结果对象，包含处理统计信息和状态
            
        Raises:
            ValueError: 当配置参数无效时
            RuntimeError: 当去重过程发生错误时
        """
        pass
    
    @abstractmethod
    async def get_deduplication_stats(self) -> Dict[str, Any]:
        """
        获取系统去重统计信息
        
        Returns:
            Dict[str, Any]: 包含系统去重统计信息的字典
        """
        pass
