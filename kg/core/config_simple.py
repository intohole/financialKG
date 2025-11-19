"""
项目核心配置模块
提供统一的配置加载和客户端创建功能
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class BaseConfig:
    """基础配置类"""

    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"


@dataclass
class AppConfig(BaseConfig):
    """应用配置"""

    APP_NAME: str = os.getenv("APP_NAME", "知识图谱API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    APP_DESCRIPTION: str = os.getenv("APP_DESCRIPTION", "知识图谱数据管理和查询服务")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = BaseConfig.DEBUG


@dataclass
class CORSConfig(BaseConfig):
    """CORS配置"""

    CORS_ORIGINS: List[str] = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(",")
    )
    CORS_ALLOW_CREDENTIALS: bool = (
        os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    )
    CORS_ALLOW_METHODS: List[str] = field(
        default_factory=lambda: os.getenv("CORS_ALLOW_METHODS", "*").split(",")
    )
    CORS_ALLOW_HEADERS: List[str] = field(
        default_factory=lambda: os.getenv("CORS_ALLOW_HEADERS", "*").split(",")
    )


@dataclass
class DatabaseConfig(BaseConfig):
    """数据库配置"""

    DB_PATH: str = os.getenv("DB_PATH", "./data/financial_kg.db")
    DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    DB_TIMEOUT: int = int(os.getenv("DB_TIMEOUT", "30"))

    def __post_init__(self):
        """初始化后处理"""
        # 确保数据库目录存在
        db_dir = Path(self.DB_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class LLMConfig(BaseConfig):
    """LLM配置"""

    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    LLM_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "3"))


@dataclass
class EmbeddingConfig(BaseConfig):
    """嵌入配置"""

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    EMBEDDING_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    EMBEDDING_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL")
    EMBEDDING_TIMEOUT: int = int(os.getenv("EMBEDDING_TIMEOUT", "30"))
    EMBEDDING_MAX_RETRIES: int = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))


@dataclass
class ChromaConfig(BaseConfig):
    """ChromaDB配置"""

    CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./chroma_db")
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "financial_kg")

    def __post_init__(self):
        """初始化后处理"""
        # 确保ChromaDB目录存在
        chroma_dir = Path(self.CHROMA_PATH)
        chroma_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class SchedulerConfig(BaseConfig):
    """调度器配置"""

    TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "Asia/Shanghai")
    MAX_WORKERS: int = int(os.getenv("SCHEDULER_MAX_WORKERS", "10"))
    COALESCE: bool = os.getenv("SCHEDULER_COALESCE", "true").lower() == "true"
    MISFIRE_GRACE_TIME: int = int(os.getenv("SCHEDULER_MISFIRE_GRACE_TIME", "300"))
    LOG_FILE: Optional[str] = os.getenv("SCHEDULER_LOG_FILE")
    LOG_FORMAT: str = os.getenv(
        "SCHEDULER_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    JOB_STORE_TYPE: str = os.getenv("SCHEDULER_JOB_STORE_TYPE", "memory")
    EXECUTOR_TYPE: str = os.getenv("SCHEDULER_EXECUTOR_TYPE", "asyncio")
    TASKS: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DeduplicationConfig(BaseConfig):
    """去重服务配置"""

    ENABLED: bool = os.getenv("DEDUPLICATION_ENABLED", "true").lower() == "true"
    AUTO_RUN: bool = os.getenv("DEDUPLICATION_AUTO_RUN", "true").lower() == "true"
    ENTITY_TYPES: List[str] = field(
        default_factory=lambda: os.getenv("DEDUPLICATION_ENTITY_TYPES", "").split(",")
    )
    SIMILARITY_THRESHOLD: float = float(
        os.getenv("DEDUPLICATION_SIMILARITY_THRESHOLD", "0.85")
    )
    BATCH_SIZE: int = int(os.getenv("DEDUPLICATION_BATCH_SIZE", "100"))
    USE_LLM: bool = os.getenv("DEDUPLICATION_USE_LLM", "true").lower() == "true"
    MAX_ENTITIES_PER_BATCH: int = int(
        os.getenv("DEDUPLICATION_MAX_ENTITIES_PER_BATCH", "1000")
    )
    RELATION_WEIGHT_THRESHOLD: float = float(
        os.getenv("DEDUPLICATION_RELATION_WEIGHT_THRESHOLD", "0.5")
    )
    MAX_GROUPS_PER_RUN: int = int(os.getenv("DEDUPLICATION_MAX_GROUPS_PER_RUN", "50"))
    LOG_LEVEL: str = os.getenv("DEDUPLICATION_LOG_LEVEL", "INFO")


@dataclass
class Config:
    """统一配置类"""

    app: AppConfig = field(default_factory=AppConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    chroma: ChromaConfig = field(default_factory=ChromaConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    deduplication: DeduplicationConfig = field(default_factory=DeduplicationConfig)

    # 全局配置项
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")

    def __getitem__(self, item):
        """支持字典式访问"""
        return getattr(self, item)


# 创建全局配置实例
config = Config()


class ConfigManager:
    """配置管理器，提供配置相关的辅助方法"""

    @staticmethod
    def get_config() -> Config:
        """获取配置实例"""
        return config

    @staticmethod
    def get_env(key: str, default: Any = None) -> Any:
        """获取环境变量"""
        return os.getenv(key, default)

    @staticmethod
    def get_file_path(filename: str, base_dir: str = ".") -> str:
        """获取文件绝对路径"""
        return str(Path(base_dir) / filename)

    @staticmethod
    def ensure_directory(path: str) -> bool:
        """确保目录存在"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    @staticmethod
    def update_config(section: str, **kwargs):
        """更新配置"""
        if hasattr(config, section):
            section_config = getattr(config, section)
            for key, value in kwargs.items():
                if hasattr(section_config, key.upper()):
                    setattr(section_config, key.upper(), value)


# 兼容旧版API
llm_config = config.llm
embedding_config = config.embedding
deduplication_config = config.deduplication
