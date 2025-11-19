"""
定时调度任务配置模块
提供任务调度相关的配置管理功能
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class TaskConfig:
    """任务配置数据类"""

    task_id: str
    task_name: str
    task_description: str = ""
    cron_expression: str = ""  # cron表达式，如 "0 */5 * * * *" 表示每5分钟执行一次
    task_active: bool = True
    max_instances: int = 1  # 最大并发实例数
    timeout: Optional[int] = None  # 超时时间(秒)，None表示不限制
    retry_count: int = 0  # 失败重试次数
    retry_delay: int = 60  # 重试延迟(秒)
    tags: List[str] = field(default_factory=list)  # 任务标签
    metadata: Dict[str, Any] = field(default_factory=dict)  # 任务元数据

    # 任务执行相关配置
    task_function: str = ""  # 任务函数路径，如 "module.submodule:function_name"
    args: List[Any] = field(default_factory=list)  # 位置参数
    kwargs: Dict[str, Any] = field(default_factory=dict)  # 关键字参数

    # 任务执行时间配置
    start_date: Optional[datetime] = None  # 开始时间
    end_date: Optional[datetime] = None  # 结束时间

    # 任务依赖配置
    depends_on: List[str] = field(default_factory=list)  # 依赖的任务ID列表
    trigger_mode: str = "date"  # 触发模式: date, interval, cron

    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.start_date, str):
            self.start_date = datetime.fromisoformat(self.start_date)
        if isinstance(self.end_date, str):
            self.end_date = datetime.fromisoformat(self.end_date)


@dataclass
class SchedulerConfig:
    """调度器配置数据类"""

    timezone: str = "Asia/Shanghai"  # 时区
    max_workers: int = 10  # 最大工作线程数
    job_defaults: Dict[str, Any] = field(default_factory=lambda: {})  # 默认任务配置
    coalesce: bool = True  # 是否合并多个相同的任务
    misfire_grace_time: int = 300  # 错过执行的宽限时间(秒)

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 持久化配置
    job_store: Dict[str, Any] = field(
        default_factory=lambda: {
            "type": "memory",  # 内存存储，可选: sqlalchemy, redis, mongodb等
            "url": None,
        }
    )

    # 执行器配置
    executor: Dict[str, Any] = field(
        default_factory=lambda: {"type": "asyncio", "max_workers": 10}  # 异步执行器
    )


class SchedulerConfigManager:
    """调度器配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为项目根目录下的scheduler_config.yaml
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "scheduler_config.yaml",
        )
        self.scheduler_config: Optional[SchedulerConfig] = None
        self.tasks: Dict[str, TaskConfig] = {}
        self.load_config()

    def load_config(self) -> None:
        """从配置文件加载配置"""
        if not os.path.exists(self.config_path):
            # 如果配置文件不存在，创建默认配置
            self.create_default_config()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # 加载调度器配置
            if "scheduler" in config_data:
                self.scheduler_config = SchedulerConfig(**config_data["scheduler"])
            else:
                self.scheduler_config = SchedulerConfig()

            # 加载任务配置
            if "tasks" in config_data:
                for task_id, task_data in config_data["tasks"].items():
                    task_data["id"] = task_id
                    self.tasks[task_id] = TaskConfig(**task_data)

        except Exception as e:
            raise ValueError(f"加载配置文件失败: {e}")

    def save_config(self) -> None:
        """保存配置到文件"""
        config_data = {
            "scheduler": {
                "timezone": self.scheduler_config.timezone,
                "max_workers": self.scheduler_config.max_workers,
                "job_defaults": self.scheduler_config.job_defaults,
                "coalesce": self.scheduler_config.coalesce,
                "misfire_grace_time": self.scheduler_config.misfire_grace_time,
                "log_level": self.scheduler_config.log_level,
                "log_file": self.scheduler_config.log_file,
                "log_format": self.scheduler_config.log_format,
                "job_store": self.scheduler_config.job_store,
                "executor": self.scheduler_config.executor,
            },
            "tasks": {},
        }

        # 保存任务配置
        for task_id, task in self.tasks.items():
            task_dict = {
                "name": task.name,
                "description": task.description,
                "cron_expression": task.cron_expression,
                "enabled": task.enabled,
                "max_instances": task.max_instances,
                "timeout": task.timeout,
                "retry_count": task.retry_count,
                "retry_delay": task.retry_delay,
                "tags": task.tags,
                "metadata": task.metadata,
                "function_path": task.function_path,
                "args": task.args,
                "kwargs": task.kwargs,
                "start_date": task.start_date.isoformat() if task.start_date else None,
                "end_date": task.end_date.isoformat() if task.end_date else None,
                "depends_on": task.depends_on,
                "trigger_mode": task.trigger_mode,
            }
            config_data["tasks"][task_id] = task_dict

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            raise ValueError(f"保存配置文件失败: {e}")

    def create_default_config(self) -> None:
        """创建默认配置文件"""
        self.scheduler_config = SchedulerConfig()

        # 创建示例任务
        example_task = TaskConfig(
            id="example_task",
            name="示例任务",
            description="这是一个示例定时任务",
            cron_expression="0 */5 * * * *",  # 每5分钟执行一次
            function_path="kg.services.scheduler.example_task",
            kwargs={"message": "Hello from scheduled task!"},
            tags=["example", "test"],
        )
        self.tasks["example_task"] = example_task

        # 保存配置
        self.save_config()

    def get_scheduler_config(self) -> SchedulerConfig:
        """获取调度器配置"""
        return self.scheduler_config

    def get_task_config(self, task_id: str) -> Optional[TaskConfig]:
        """获取指定任务配置"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, TaskConfig]:
        """获取所有任务配置"""
        return self.tasks

    def add_task(self, task: TaskConfig) -> None:
        """添加任务配置"""
        self.tasks[task.id] = task
        self.save_config()

    def update_task(self, task_id: str, **kwargs) -> bool:
        """更新任务配置"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        self.save_config()
        return True

    def remove_task(self, task_id: str) -> bool:
        """删除任务配置"""
        if task_id not in self.tasks:
            return False

        del self.tasks[task_id]
        self.save_config()
        return True

    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        return self.update_task(task_id, enabled=True)

    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        return self.update_task(task_id, enabled=False)

    def get_tasks_by_tag(self, tag: str) -> Dict[str, TaskConfig]:
        """根据标签获取任务"""
        return {
            task_id: task for task_id, task in self.tasks.items() if tag in task.tags
        }

    def get_enabled_tasks(self) -> Dict[str, TaskConfig]:
        """获取所有启用的任务"""
        return {task_id: task for task_id, task in self.tasks.items() if task.enabled}
