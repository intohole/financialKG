"""
项目核心配置模块
提供统一的配置加载和客户端创建功能
"""
import os
from typing import Optional, Dict, Any, List
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field


class BaseConfig:
    """配置基础类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的config.yaml
        """
        self.config_path = config_path or os.path.join(
            Path(__file__).parent.parent.parent, "config.yaml"
        )
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """
        加载配置文件
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config or {}
        except FileNotFoundError:
            # 如果配置文件不存在，使用默认配置
            return {
                'llm': {
                    'model': 'gpt-3.5-turbo',
                    'api_key': os.getenv('OPENAI_API_KEY'),
                    'base_url': os.getenv('OPENAI_BASE_URL'),
                    'timeout': 30,
                    'max_retries': 3,
                    'temperature': 0.1,
                    'max_tokens': 2048
                },
                'scheduler': {
                    'timezone': "Asia/Shanghai",
                    'max_workers': 10,
                    'coalesce': True,
                    'misfire_grace_time': 300,
                    'log_level': "INFO",
                    'log_file': None,
                    'log_format': "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    'job_store': {
                        'type': 'memory',
                        'url': None
                    },
                    'executor': {
                        'type': 'asyncio',
                        'max_workers': 10
                    },
                    'tasks': []
                }
            }
        except Exception as e:
            raise ValueError(f"加载配置文件失败: {e}")
    
    @property
    def model(self) -> str:
        """
        获取模型名称
        """
        return self.config.get('llm', {}).get('model', 'gpt-3.5-turbo')
    
    @property
    def api_key(self) -> Optional[str]:
        """
        获取API密钥
        """
        return self.config.get('llm', {}).get('api_key') or os.getenv('OPENAI_API_KEY')
    
    @property
    def base_url(self) -> Optional[str]:
        """
        获取API基础URL
        """
        return self.config.get('llm', {}).get('base_url') or os.getenv('OPENAI_BASE_URL')
    
    @property
    def temperature(self) -> float:
        """
        获取温度参数
        """
        return self.config.get('llm', {}).get('temperature', 0.1)
    
    @property
    def max_tokens(self) -> int:
        """
        获取最大令牌数
        """
        return self.config.get('llm', {}).get('max_tokens', 2048)
    
    @property
    def timeout(self) -> int:
        """
        获取超时时间
        """
        return self.config.get('llm', {}).get('timeout', 30)
    
    @property
    def max_retries(self) -> int:
        """
        获取最大重试次数
        """
        return self.config.get('llm', {}).get('max_retries', 3)


class LLMConfig(BaseConfig):
    """大模型配置类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化大模型配置
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的config.yaml
        """
        super().__init__(config_path)
        # 延迟初始化客户端
        self._client = None
    
    def _init_client(self):
        """
        初始化OpenAI客户端
        """
        if self._client is not None:
            return self._client

        from openai import OpenAI
        
        if not self.api_key:
            raise ValueError("未找到OpenAI API密钥，请在配置文件中设置或通过环境变量OPENAI_API_KEY提供")
        
        client_config = {
            'api_key': self.api_key,
            'timeout': self.timeout,
            'max_retries': self.max_retries
        }
        
        if self.base_url:
            client_config['base_url'] = self.base_url
            
        self._client = OpenAI(**client_config)
        return self._client

    @property
    def client(self):
        """
        获取OpenAI客户端实例
        """
        return self._init_client()
    
    def get_client(self):
        """
        获取OpenAI客户端
        """
        return self.client


class TaskConfig:
    """任务配置类"""
    
    def __init__(self, task_id: str, task_name: str, task_type: str, task_function: str,
                 task_params: Dict[str, Any] = None, task_trigger: Dict[str, Any] = None,
                 task_dependencies: List[str] = None, task_priority: int = 5, task_active: bool = True,
                 task_description: str = "", task_metadata: Dict[str, Any] = None, **kwargs):
        self.task_id = task_id
        self.task_name = task_name
        self.task_type = task_type
        self.task_function = task_function
        self.task_params = task_params or {}
        self.task_trigger = task_trigger or {}
        self.task_dependencies = task_dependencies or []
        self.task_priority = task_priority
        self.task_active = task_active
        self.task_description = task_description
        self.task_metadata = task_metadata or {}
        
        # 处理额外参数
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """将任务配置转换为字典"""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "task_type": self.task_type,
            "task_function": self.task_function,
            "task_params": self.task_params,
            "task_trigger": self.task_trigger,
            "task_dependencies": self.task_dependencies,
            "task_priority": self.task_priority,
            "task_active": self.task_active,
            "task_description": self.task_description,
            "task_metadata": self.task_metadata
        }
    
    @classmethod
    def from_dict(cls, task_dict: Dict[str, Any]) -> "TaskConfig":
        """从字典创建任务配置"""
        return cls(**task_dict)


class SchedulerConfig:
    """调度器配置类"""
    
    def __init__(self, timezone: str = "Asia/Shanghai", max_workers: int = 10,
                 coalesce: bool = True, misfire_grace_time: int = 300,
                 log_level: str = "INFO", log_file: Optional[str] = None,
                 log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                 job_store: Dict[str, Any] = None, executor: Dict[str, Any] = None,
                 tasks: List[TaskConfig] = None):
        self.timezone = timezone
        self.max_workers = max_workers
        self.coalesce = coalesce
        self.misfire_grace_time = misfire_grace_time
        self.log_level = log_level
        self.log_file = log_file
        self.log_format = log_format
        self.job_store = job_store or {'type': 'memory', 'url': None}
        self.executor = executor or {'type': 'asyncio', 'max_workers': 10}
        self.tasks = tasks or []
    
    def to_dict(self) -> Dict[str, Any]:
        """将调度器配置转换为字典"""
        return {
            "timezone": self.timezone,
            "max_workers": self.max_workers,
            "coalesce": self.coalesce,
            "misfire_grace_time": self.misfire_grace_time,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "log_format": self.log_format,
            "job_store": self.job_store,
            "executor": self.executor,
            "tasks": [task.to_dict() for task in self.tasks]
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SchedulerConfig":
        """从字典创建调度器配置"""
        tasks = []
        if "tasks" in config_dict:
            for task_dict in config_dict["tasks"]:
                tasks.append(TaskConfig.from_dict(task_dict))
        
        return cls(
            timezone=config_dict.get("timezone", "Asia/Shanghai"),
            max_workers=config_dict.get("max_workers", 10),
            coalesce=config_dict.get("coalesce", True),
            misfire_grace_time=config_dict.get("misfire_grace_time", 300),
            log_level=config_dict.get("log_level", "INFO"),
            log_file=config_dict.get("log_file"),
            log_format=config_dict.get("log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            job_store=config_dict.get("job_store"),
            executor=config_dict.get("executor"),
            tasks=tasks
        )


class SchedulerConfigManager:
    """调度器配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            Path(__file__).parent.parent.parent, "config.yaml"
        )
    
    def load_config(self) -> SchedulerConfig:
        """加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f) or {}
            
            scheduler_config_dict = config_dict.get("scheduler", {})
            return SchedulerConfig.from_dict(scheduler_config_dict)
        except Exception as e:
            print(f"加载配置失败: {e}, 使用默认配置")
            return SchedulerConfig()
    
    def save_config(self, scheduler_config: SchedulerConfig) -> None:
        """保存配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f) or {}
            
            config_dict["scheduler"] = scheduler_config.to_dict()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def add_task(self, task_config: TaskConfig) -> None:
        """添加任务配置"""
        scheduler_config = self.load_config()
        scheduler_config.tasks.append(task_config)
        self.save_config(scheduler_config)
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务配置"""
        scheduler_config = self.load_config()
        initial_length = len(scheduler_config.tasks)
        scheduler_config.tasks = [task for task in scheduler_config.tasks if task.task_id != task_id]
        
        if len(scheduler_config.tasks) < initial_length:
            self.save_config(scheduler_config)
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[TaskConfig]:
        """获取任务配置"""
        scheduler_config = self.load_config()
        for task in scheduler_config.tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def update_task(self, task_config: TaskConfig) -> bool:
        """更新任务配置"""
        scheduler_config = self.load_config()
        for i, task in enumerate(scheduler_config.tasks):
            if task.task_id == task_config.task_id:
                scheduler_config.tasks[i] = task_config
                self.save_config(scheduler_config)
                return True
        return False


class SchedulerConfigWrapper(BaseConfig):
    """调度器配置包装类，用于访问项目核心配置中的调度器配置"""
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
    
    @property
    def timezone(self) -> str:
        return self.config.get('scheduler', {}).get('timezone', "Asia/Shanghai")
    
    @property
    def max_workers(self) -> int:
        return self.config.get('scheduler', {}).get('max_workers', 10)
    
    @property
    def coalesce(self) -> bool:
        return self.config.get('scheduler', {}).get('coalesce', True)
    
    @property
    def misfire_grace_time(self) -> int:
        return self.config.get('scheduler', {}).get('misfire_grace_time', 300)
    
    @property
    def log_level(self) -> str:
        return self.config.get('scheduler', {}).get('log_level', "INFO")
    
    @property
    def log_file(self) -> Optional[str]:
        return self.config.get('scheduler', {}).get('log_file')
    
    @property
    def log_format(self) -> str:
        return self.config.get('scheduler', {}).get('log_format', "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    @property
    def job_store(self) -> Dict[str, Any]:
        return self.config.get('scheduler', {}).get('job_store', {'type': 'memory', 'url': None})
    
    @property
    def executor(self) -> Dict[str, Any]:
        return self.config.get('scheduler', {}).get('executor', {'type': 'asyncio', 'max_workers': 10})
    
    @property
    def tasks(self) -> List[Dict[str, Any]]:
        return self.config.get('scheduler', {}).get('tasks', [])


# 全局配置实例
llm_config = LLMConfig()
scheduler_config_manager = SchedulerConfigManager()
scheduler_config = SchedulerConfigWrapper()
