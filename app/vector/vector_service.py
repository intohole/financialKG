"""
向量搜索服务管理类
负责向量搜索实例的创建、管理和配置
"""

import logging
from typing import Dict, Any, Optional, Union
from threading import Lock

from app.config.config_manager import ConfigManager, VectorSearchConfig
from app.vector.base import VectorSearchBase
from app.vector.chroma_vector_search import ChromaVectorSearch
from app.vector.exceptions import VectorSearchError


logger = logging.getLogger(__name__)


class VectorSearchService:
    """
    向量搜索服务管理类
    实现单例模式，负责管理向量搜索实例的生命周期
    """
    
    _instance = None
    _lock = Lock()

    def __new__(cls, config_manager: Optional[ConfigManager] = None):
        """
        单例模式实现
        
        Args:
            config_manager: 配置管理器实例
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VectorSearchService, cls).__new__(cls)
                cls._instance._initialize(config_manager)
            return cls._instance

    def _initialize(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化服务
        
        Args:
            config_manager: 配置管理器实例
        """
        self._config_manager = config_manager or ConfigManager()
        self._vector_search_instances: Dict[str, VectorSearchBase] = {}
        self._config_cache: Optional[VectorSearchConfig] = None
        self._initialized = False
        
        # 注册配置变更回调
        self._config_manager.add_change_callback(self._on_config_change)
        self._initialized = True
        logger.info("向量搜索服务初始化完成")

    def _on_config_change(self):
        """
        配置变更回调
        当配置文件更新时重新创建向量搜索实例
        """
        logger.info("检测到配置变更，重建向量搜索实例")
        self._config_cache = None
        # 关闭现有实例
        for name, instance in self._vector_search_instances.items():
            try:
                instance.close()
                logger.info(f"已关闭向量搜索实例: {name}")
            except Exception as e:
                logger.error(f"关闭向量搜索实例失败: {name}, 错误: {str(e)}")
        
        # 清空实例缓存
        self._vector_search_instances.clear()

    def get_vector_search_config(self) -> VectorSearchConfig:
        """
        获取向量搜索配置
        
        Returns:
            VectorSearchConfig: 向量搜索配置对象
        """
        if self._config_cache is None:
            self._config_cache = self._config_manager.get_vector_search_config()
        return self._config_cache

    def get_vector_search(self, instance_name: str = "default") -> VectorSearchBase:
        """
        获取向量搜索实例
        
        Args:
            instance_name: 实例名称
            
        Returns:
            VectorSearchBase: 向量搜索实例
            
        Raises:
            VectorSearchError: 当创建向量搜索实例失败时
        """
        # 检查实例是否已存在
        if instance_name in self._vector_search_instances:
            return self._vector_search_instances[instance_name]
        
        # 创建新实例
        try:
            config = self.get_vector_search_config()
            vector_search = self._create_vector_search(config, instance_name)
            self._vector_search_instances[instance_name] = vector_search
            logger.info(f"成功创建向量搜索实例: {instance_name}, 类型: {config.type}")
            return vector_search
        except Exception as e:
            logger.error(f"创建向量搜索实例失败: {str(e)}")
            raise VectorSearchError(f"创建向量搜索实例失败: {str(e)}")

    def _create_vector_search(self, config: VectorSearchConfig, instance_name: str) -> VectorSearchBase:
        """
        根据配置创建向量搜索实例
        
        Args:
            config: 向量搜索配置
            instance_name: 实例名称
            
        Returns:
            VectorSearchBase: 向量搜索实例
            
        Raises:
            VectorSearchError: 当不支持的向量数据库类型时
        """
        # 根据类型创建相应的向量搜索实例
        if config.type.lower() == 'chroma':
            return self._create_chroma_instance(config, instance_name)
        elif config.type.lower() == 'pinecone':
            # 预留支持Pinecone的接口
            raise VectorSearchError("Pinecone支持尚未实现")
        elif config.type.lower() == 'weaviate':
            # 预留支持Weaviate的接口
            raise VectorSearchError("Weaviate支持尚未实现")
        else:
            raise VectorSearchError(f"不支持的向量数据库类型: {config.type}")

    def _create_chroma_instance(self, config: VectorSearchConfig, instance_name: str) -> ChromaVectorSearch:
        """
        创建Chroma向量搜索实例
        
        Args:
            config: 向量搜索配置
            instance_name: 实例名称
            
        Returns:
            ChromaVectorSearch: Chroma向量搜索实例
        """
        # 构建Chroma配置参数
        chroma_kwargs = {
            'path': config.path,
            'metric': config.metric,
            'timeout': config.timeout,
            'anonymized_telemetry': False
        }
        
        # 添加远程连接参数（如果有）
        if config.host:
            chroma_kwargs['host'] = config.host
        if config.port:
            chroma_kwargs['port'] = config.port
        
        # 创建并返回实例
        return ChromaVectorSearch(**chroma_kwargs)

    def create_index(self, index_name: str, dimension: int, **kwargs) -> bool:
        """
        创建向量索引的便捷方法
        
        Args:
            index_name: 索引名称
            dimension: 向量维度
            **kwargs: 其他索引配置参数
            
        Returns:
            bool: 创建是否成功
        """
        vector_search = self.get_vector_search()
        return vector_search.create_index(index_name, dimension, **kwargs)

    def search(self, index_name: str, query_vector: list, top_k: int = 10, **kwargs) -> list:
        """
        搜索向量的便捷方法
        
        Args:
            index_name: 索引名称
            query_vector: 查询向量
            top_k: 返回结果数量
            **kwargs: 其他搜索参数
            
        Returns:
            list: 搜索结果列表
        """
        vector_search = self.get_vector_search()
        return vector_search.search_vectors(index_name, query_vector, top_k, **kwargs)

    def add_vectors(self, index_name: str, vectors: list, ids: list, **kwargs) -> bool:
        """
        添加向量的便捷方法
        
        Args:
            index_name: 索引名称
            vectors: 向量列表
            ids: ID列表
            **kwargs: 其他参数
            
        Returns:
            bool: 添加是否成功
        """
        vector_search = self.get_vector_search()
        return vector_search.add_vectors(index_name, vectors, ids, **kwargs)

    def list_instances(self) -> list:
        """
        列出所有向量搜索实例
        
        Returns:
            list: 实例名称列表
        """
        return list(self._vector_search_instances.keys())

    def close_instance(self, instance_name: str) -> bool:
        """
        关闭指定的向量搜索实例
        
        Args:
            instance_name: 实例名称
            
        Returns:
            bool: 关闭是否成功
        """
        if instance_name in self._vector_search_instances:
            try:
                self._vector_search_instances[instance_name].close()
                del self._vector_search_instances[instance_name]
                logger.info(f"已关闭并移除向量搜索实例: {instance_name}")
                return True
            except Exception as e:
                logger.error(f"关闭向量搜索实例失败: {str(e)}")
                return False
        return False

    def close_all(self) -> None:
        """
        关闭所有向量搜索实例
        """
        for instance_name in list(self._vector_search_instances.keys()):
            self.close_instance(instance_name)
        logger.info("已关闭所有向量搜索实例")

    def refresh_config(self) -> None:
        """
        刷新配置并重建实例
        """
        self._config_cache = None
        self._config_manager.reload()
        logger.info("向量搜索服务配置已刷新")

    def __del__(self):
        """
        析构函数，确保资源释放
        """
        self.close_all()

    def __enter__(self):
        """
        上下文管理器入口
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        """
        self.close_all()
