"""
配置管理器
提供YAML配置文件的加载、解析、缓存和变更监听功能
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable, List
from dataclasses import dataclass
from threading import Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.exceptions.base_exceptions import BaseException
from app.utils.logging_utils import get_logger


logger = get_logger(__name__)





@dataclass
class LLMConfig:
    """大模型配置"""
    model: str
    api_key: str
    base_url: str
    timeout: int
    max_retries: int
    temperature: float
    max_tokens: int


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str
    echo: bool
    pool_pre_ping: bool
    pool_recycle: int


@dataclass
class APIConfig:
    """API服务配置"""
    host: str
    port: int
    debug: bool
    reload: bool
    workers: int
    log_level: str


@dataclass
class SchedulerConfig:
    """调度器配置"""
    timezone: str
    max_workers: int
    coalesce: bool
    misfire_grace_time: int
    log_level: str
    log_file: Optional[str]
    log_format: str


@dataclass
class LoggingConfig:
    """日志配置"""
    version: int
    disable_existing_loggers: bool
    formatters: Dict[str, Any]
    handlers: Dict[str, Any]
    loggers: Dict[str, Any]
    root: Dict[str, Any]


@dataclass
class NewsProcessingConfig:
    """新闻处理配置"""
    batch_size: int
    max_retries: int
    retry_delay: int
    timeout: int
    sources: List[Dict[str, Any]]
    update_interval: int

@dataclass
class ItemWithDescription:
    """
    带描述的配置项
    """
    name: str
    description: str = None

    def to_markdown(self):
        return f"- **{self.name}**: {self.description}"


@dataclass
class CategoryConfigItem:
    """
    类别配置项
    """
    category: ItemWithDescription
    relation_types: list[ItemWithDescription]
    entity_types: list[ItemWithDescription]

    def get_relation_types_prompt(self):
        return "\n".join([ f"- {relation_type.name}: {relation_type.description}" for relation_type in self.relation_types])

    def get_entity_types_prompt(self):
        return "\n".join([ f"- {entity_type.name}: {entity_type.description}" for entity_type in self.entity_types])




@dataclass
class EntityMergingConfig:
    """
    实体合并配置
    """
    enabled: bool
    similarity_threshold: float
    max_candidates: int


@dataclass
class KnowledgeGraphConfig:
    """
    知识图谱配置
    支持多类别的知识图谱配置
    """
    categories: Dict[str, CategoryConfigItem]
    default_category: str
    similarity_threshold: float
    max_entities_per_news: int
    entity_merging: EntityMergingConfig


    def get_categories_prompt(self):
        return "\n".join([ f"- {category_key} : {category.category.description}" for category_key,category in self.categories.items()])


@dataclass
class EmbeddingConfig:
    """
    嵌入模型配置
    """
    model: str
    api_key: str
    base_url: str
    timeout: int
    max_retries: int
    dimension: Optional[int] = None  # 嵌入维度
    normalize: bool = True  # 是否归一化向量
    secret_key: Optional[str] = None  # 额外密钥（如百度千帆需要）
    endpoint: Optional[str] = None  # API端点


@dataclass
class CacheConfig:
    """缓存配置"""
    type: str
    ttl: int
    max_size: int
    redis: Dict[str, Any]


@dataclass
class VectorSearchConfig:
    """
    向量搜索配置
    """
    type: str  # 向量数据库类型，如 'chroma', 'pinecone', 'weaviate' 等
    path: str  # 本地路径，用于chroma等本地向量数据库
    host: Optional[str] = None  # 主机地址，用于远程向量数据库
    port: Optional[int] = None  # 端口号
    api_key: Optional[str] = None  # API密钥
    timeout: int = 30  # 超时时间（秒）
    collection_name: str = "default"  # 默认集合名称
    dimension: int = 1536  # 默认向量维度
    metric: str = "cosine"  # 距离度量方式，如 'cosine', 'euclidean', 'l2' 等
    embedding_model: Optional[str] = None  # 关联的嵌入模型名称


@dataclass
class SecurityConfig:
    """安全配置"""
    secret_key: Optional[str]
    algorithm: str
    access_token_expire_minutes: int
    cors_origins: List[str]


class ConfigChangeHandler(FileSystemEventHandler):
    """配置文件变更处理器"""
    
    def __init__(self, callback: Callable[[], None]):
        self.callback = callback
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.yaml'):
            logger.info(f"配置文件已变更: {event.src_path}")
            self.callback()


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self._config_path = Path(config_path or self._get_default_config_path())
        self._config_data: Optional[Dict[str, Any]] = None
        self._cache_lock = Lock()
        self._last_modified: Optional[float] = None
        self._observer: Optional[Observer] = None
        self._change_callbacks: List[Callable[[], None]] = []
        
        # 确保配置文件存在
        if not self._config_path.exists():
            raise BaseException(f"配置文件不存在: {self._config_path}", error_code="CONFIG_NOT_FOUND_ERROR")
    
    def _get_default_config_path(self) -> Path:
        """获取默认配置文件路径"""
        # 优先使用环境变量指定的路径
        env_path = os.getenv('CONFIG_PATH')
        if env_path:
            return Path(env_path)
        
        # 使用项目根目录下的config.yaml
        project_root = Path(__file__).parent.parent.parent
        return project_root / 'config.yaml'
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise BaseException(f"YAML解析错误: {e}", error_code="CONFIG_FORMAT_ERROR")
        except Exception as e:
            raise BaseException(f"配置文件读取错误: {e}", error_code="CONFIG_LOAD_ERROR")
    
    def _should_reload(self) -> bool:
        """检查是否需要重新加载配置"""
        try:
            current_modified = self._config_path.stat().st_mtime
            return self._last_modified is None or current_modified > self._last_modified
        except Exception:
            return True
    
    def _update_cache(self):
        """更新配置缓存"""
        with self._cache_lock:
            if self._should_reload():
                logger.debug("重新加载配置文件")
                self._config_data = self._load_config()
                self._last_modified = self._config_path.stat().st_mtime
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置数据"""
        if self._config_data is None or self._should_reload():
            self._update_cache()
        return self._config_data or {}
    
    def reload(self):
        """强制重新加载配置"""
        logger.info("强制重新加载配置文件")
        self._update_cache()
        self._notify_change()
    
    def _notify_change(self):
        """通知配置变更"""
        for callback in self._change_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"配置变更回调执行失败: {e}")
    
    def add_change_callback(self, callback: Callable[[], None]):
        """添加配置变更回调"""
        self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[], None]):
        """移除配置变更回调"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def start_watching(self):
        """开始监听配置文件变更"""
        if self._observer is not None:
            return
        
        self._observer = Observer()
        handler = ConfigChangeHandler(self.reload)
        self._observer.schedule(handler, str(self._config_path.parent), recursive=False)
        self._observer.start()
        logger.info(f"开始监听配置文件变更: {self._config_path}")
    
    def stop_watching(self):
        """停止监听配置文件变更"""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("停止监听配置文件变更")
    
    # 类型安全的配置访问方法
    def get_llm_config(self) -> LLMConfig:
        """获取大模型配置"""
        config = self.get_config().get('llm', {})
        return LLMConfig(
            model=config.get('model', ''),
            api_key=config.get('api_key', ''),
            base_url=config.get('base_url', ''),
            timeout=config.get('timeout', 30),
            max_retries=config.get('max_retries', 3),
            temperature=config.get('temperature', 0.1),
            max_tokens=config.get('max_tokens', 2048)
        )
    
    def get_database_config(self) -> DatabaseConfig:
        """获取数据库配置"""
        config = self.get_config().get('database', {})
        return DatabaseConfig(
            url=config.get('url', ''),
            echo=config.get('echo', False),
            pool_pre_ping=config.get('pool_pre_ping', True),
            pool_recycle=config.get('pool_recycle', 3600)
        )
    
    def get_api_config(self) -> APIConfig:
        """获取API服务配置"""
        config = self.get_config().get('api', {})
        return APIConfig(
            host=config.get('host', '0.0.0.0'),
            port=config.get('port', 8000),
            debug=config.get('debug', True),
            reload=config.get('reload', False),
            workers=config.get('workers', 1),
            log_level=config.get('log_level', 'info')
        )
    
    def get_logging_config(self) -> LoggingConfig:
        """获取日志配置"""
        config = self.get_config().get('logging', {})
        try:
            return LoggingConfig(
                version=config.get('version', 1),
                disable_existing_loggers=config.get('disable_existing_loggers', False),
                formatters=config.get('formatters', {}),
                handlers=config.get('handlers', {}),
                loggers=config.get('loggers', {}),
                root=config.get('root', {})
            )
        except Exception as e:
            raise BaseException(f"日志配置错误: {e}", error_code="CONFIGURATION_ERROR")
    
    def get_news_processing_config(self) -> NewsProcessingConfig:
        """获取新闻处理配置"""
        config = self.get_config().get('news_processing', {})
        return NewsProcessingConfig(
            batch_size=config.get('batch_size', 10),
            max_retries=config.get('max_retries', 3),
            retry_delay=config.get('retry_delay', 1),
            timeout=config.get('timeout', 30),
            sources=config.get('sources', []),
            update_interval=config.get('update_interval', 3600)
        )
    
    def get_knowledge_graph_config(self) -> KnowledgeGraphConfig:
        """获取知识图谱配置"""
        config = self.get_config().get('knowledge_graph', {})
        
        # 构建类别配置
        categories_config = config.get('categories', {})
        categories = {}
        
        for cat_key, cat_data in categories_config.items():
            # 构建类别基本信息
            category_item = ItemWithDescription(
                name=cat_data.get('name', ''),
                description=cat_data.get('description', '')
            )
            
            # 构建关系类型列表
            relation_types = [
                ItemWithDescription(name=rel_type) 
                for rel_type in cat_data.get('relation_types', [])
            ]
            
            # 构建实体类型列表
            entity_types = [
                ItemWithDescription(name=ent_type) 
                for ent_type in cat_data.get('entity_types', [])
            ]
            
            # 构建类别配置项
            categories[cat_key] = CategoryConfigItem(
                category=category_item,
                relation_types=relation_types,
                entity_types=entity_types
            )
        
        # 构建实体合并配置
        entity_merging_config = config.get('entity_merging', {})
        entity_merging = EntityMergingConfig(
            enabled=entity_merging_config.get('enabled', True),
            similarity_threshold=entity_merging_config.get('similarity_threshold', 0.85),
            max_candidates=entity_merging_config.get('max_candidates', 5)
        )
        
        return KnowledgeGraphConfig(
            categories=categories,
            default_category=config.get('default_category', 'financial'),
            similarity_threshold=config.get('similarity_threshold', 0.7),
            max_entities_per_news=config.get('max_entities_per_news', 50),
            entity_merging=entity_merging
        )
    
    def get_cache_config(self) -> CacheConfig:
        """
        获取缓存配置
        """
        config = self.get_config().get('cache', {})
        return CacheConfig(
            type=config.get('type', 'memory'),
            ttl=config.get('ttl', 3600),
            max_size=config.get('max_size', 1000),
            redis=config.get('redis', {})
        )
    
    def get_embedding_config(self) -> EmbeddingConfig:
        """
        获取嵌入模型配置
        如果没有专门的embedding配置，则使用llm配置作为默认值
        """
        config = self.get_config().get('embedding', {})
        # 如果没有专门的embedding配置，使用llm配置作为默认值
        llm_config = self.get_config().get('llm', {})
        return EmbeddingConfig(
            model=config.get('model', llm_config.get('model', 'text-embedding-ada-002')),
            api_key=config.get('api_key', llm_config.get('api_key', '')),
            base_url=config.get('base_url', llm_config.get('base_url', '')),
            timeout=config.get('timeout', llm_config.get('timeout', 30)),
            max_retries=config.get('max_retries', llm_config.get('max_retries', 3)),
            dimension=config.get('dimension'),
            normalize=config.get('normalize', True),
            secret_key=config.get('secret_key'),
            endpoint=config.get('endpoint')
        )
    
    def get_security_config(self) -> SecurityConfig:
        """获取安全配置"""
        config = self.get_config().get('security', {})
        return SecurityConfig(
            secret_key=config.get('secret_key'),
            algorithm=config.get('algorithm', 'HS256'),
            access_token_expire_minutes=config.get('access_token_expire_minutes', 30),
            cors_origins=config.get('cors_origins', [])
        )
    
    def get_vector_search_config(self) -> VectorSearchConfig:
        """
        获取向量搜索配置
        """
        config = self.get_config().get('vector_search', {})
        return VectorSearchConfig(
            type=config.get('type', 'chroma'),
            path=config.get('path', './data/chroma'),
            host=config.get('host'),
            port=config.get('port'),
            api_key=config.get('api_key'),
            timeout=config.get('timeout', 30),
            collection_name=config.get('collection_name', 'default'),
            dimension=config.get('dimension', 1536),
            metric=config.get('metric', 'cosine'),
            embedding_model=config.get('embedding_model')
        )
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_watching()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_watching()