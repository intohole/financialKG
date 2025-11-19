"""
任务协调器
统一管理任务的创建、执行和监控
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from kg.core.config import scheduler_config, scheduler_config_manager

from .async_scheduler import AsyncTaskScheduler
from .scheduler_config import SchedulerConfigManager, TaskConfig
from .task_manager import TaskExecutionInfo, TaskManager, TaskPriority


class TaskTriggerType(str, Enum):
    """任务触发类型"""

    CRON = "cron"
    INTERVAL = "interval"
    DATE = "date"
    FUNCTION = "function"


class TaskCoordinator:
    """任务协调器，统一管理任务的创建、执行和监控"""

    def __init__(self, config_manager: Optional[SchedulerConfigManager] = None):
        """
        初始化任务协调器

        Args:
            config_manager: 配置管理器实例，默认为None
        """
        self.config_manager = config_manager or scheduler_config_manager
        self.scheduler = AsyncTaskScheduler(self.config_manager)
        self.task_manager = TaskManager(self.scheduler)
        self.logger = self.scheduler.logger

    async def start(self) -> bool:
        """
        启动任务协调器

        Returns:
            是否成功启动
        """
        try:
            await self.scheduler.start()
            self.logger.info("任务协调器已启动")
            return True
        except Exception as e:
            self.logger.error(f"启动任务协调器失败: {e}")
            return False

    async def stop(self) -> bool:
        """
        停止任务协调器

        Returns:
            是否成功停止
        """
        try:
            await self.scheduler.stop()
            self.logger.info("任务协调器已停止")
            return True
        except Exception as e:
            self.logger.error(f"停止任务协调器失败: {e}")
            return False

    async def add_cron_task(
        self,
        task_name: str,
        task_function: Union[str, Callable],
        cron_expression: str,
        task_params: Optional[Dict[str, Any]] = None,
        task_priority: int = 5,
        task_active: bool = True,
        task_description: str = "",
        max_retries: int = 0,
        retry_delay: int = 60,
        timeout: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """
        添加定时任务

        Args:
            task_name: 任务名称
            task_function: 任务函数或函数路径
            cron_expression: Cron表达式
            task_params: 任务参数
            task_priority: 任务优先级
            task_active: 是否激活任务
            task_description: 任务描述
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            timeout: 超时时间(秒)
            start_date: 开始时间
            end_date: 结束时间

        Returns:
            任务ID
        """
        task_id = f"task_{int(time.time())}_{task_name.replace(' ', '_')}"

        # 处理任务函数
        if callable(task_function):
            func = task_function.__name__
        else:
            func = task_function

        task_config = TaskConfig(
            task_id=task_id,
            task_name=task_name,
            task_type="cron",
            task_function=func,
            task_params=task_params or {},
            task_trigger={
                "type": "cron",
                "expression": cron_expression,
                "start_date": start_date,
                "end_date": end_date,
            },
            task_dependencies=[],
            task_priority=task_priority,
            task_active=task_active,
            task_description=task_description,
        )

        # 添加任务到调度器
        success = await self.scheduler.add_task(task_config)
        if not success:
            raise ValueError(f"添加任务失败: {task_id}")

        self.logger.info(f"已添加定时任务: {task_id} ({task_name})")
        return task_id

    async def add_interval_task(
        self,
        task_name: str,
        task_function: Union[str, Callable],
        interval: int,
        task_params: Optional[Dict[str, Any]] = None,
        task_priority: int = 5,
        task_active: bool = True,
        task_description: str = "",
        tags: Optional[List[str]] = None,
        max_retries: int = 0,
        retry_delay: int = 60,
        timeout: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """
        添加间隔任务

        Args:
            task_name: 任务名称
            task_function: 任务函数或函数路径
            interval: 执行间隔(秒)
            task_params: 任务参数
            task_priority: 任务优先级
            task_active: 是否激活任务
            task_description: 任务描述
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            timeout: 超时时间(秒)
            start_date: 开始时间
            end_date: 结束时间

        Returns:
            任务ID
        """
        task_id = f"task_{int(time.time())}_{task_name.replace(' ', '_')}"

        # 处理任务函数
        if callable(task_function):
            func = task_function.__name__
        else:
            func = task_function

        task_config = TaskConfig(
            task_id=task_id,
            task_name=task_name,
            task_type="interval",
            task_function=func,
            task_params=task_params or {},
            task_trigger={
                "type": "interval",
                "seconds": interval,
                "start_date": start_date,
                "end_date": end_date,
            },
            task_dependencies=[],
            task_priority=task_priority,
            task_active=task_active,
            task_description=task_description,
        )

        # 添加任务到调度器
        success = await self.scheduler.add_task(task_config)
        if not success:
            raise ValueError(f"添加任务失败: {task_id}")

        self.logger.info(f"已添加间隔任务: {task_id} ({task_name})")
        return task_id

    async def add_one_time_task(
        self,
        task_name: str,
        task_function: Union[str, Callable],
        run_date: datetime,
        task_params: Optional[Dict[str, Any]] = None,
        task_priority: int = 5,
        task_active: bool = True,
        task_description: str = "",
        max_retries: int = 0,
        retry_delay: int = 60,
        timeout: Optional[int] = None,
    ) -> str:
        """
        添加一次性任务

        Args:
            task_name: 任务名称
            task_function: 任务函数或函数路径
            run_date: 执行时间
            task_params: 任务参数
            task_priority: 任务优先级
            task_active: 是否激活任务
            task_description: 任务描述
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            timeout: 超时时间(秒)

        Returns:
            任务ID
        """
        task_id = f"task_{int(time.time())}_{task_name.replace(' ', '_')}"

        # 处理任务函数
        if callable(task_function):
            func = task_function.__name__
        else:
            func = task_function

        task_config = TaskConfig(
            task_id=task_id,
            task_name=task_name,
            task_type="date",
            task_function=func,
            task_params=task_params or {},
            task_trigger={"type": "date", "run_date": run_date},
            task_dependencies=[],
            task_priority=task_priority,
            task_active=task_active,
            task_description=task_description,
        )

        # 添加任务到调度器
        success = await self.scheduler.add_task(task_config)
        if not success:
            raise ValueError(f"添加任务失败: {task_id}")

        self.logger.info(f"已添加一次性任务: {task_id} ({task_name})")
        return task_id

    async def add_function_task(
        self,
        task_name: str,
        task_function: Union[str, Callable],
        task_params: Optional[Dict[str, Any]] = None,
        task_priority: int = 5,
        task_active: bool = True,
        task_description: str = "",
        max_retries: int = 0,
        retry_delay: int = 60,
        timeout: Optional[int] = None,
    ) -> str:
        """
        添加普通函数任务

        Args:
            task_name: 任务名称
            task_function: 任务函数或函数路径
            task_params: 任务参数
            task_priority: 任务优先级
            task_active: 是否激活任务
            task_description: 任务描述
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            timeout: 超时时间(秒)

        Returns:
            任务ID
        """
        task_id = f"task_{int(time.time())}_{task_name.replace(' ', '_')}"

        # 处理任务函数
        if callable(task_function):
            func = task_function.__name__
        else:
            func = task_function

        task_config = TaskConfig(
            task_id=task_id,
            task_name=task_name,
            task_type="function",
            task_function=func,
            task_params=task_params or {},
            task_trigger={},
            task_dependencies=[],
            task_priority=task_priority,
            task_active=task_active,
            task_description=task_description,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
        )

        # 添加任务到调度器
        success = await self.scheduler.add_task(task_config)
        if not success:
            raise ValueError(f"添加任务失败: {task_id}")

        self.logger.info(f"已添加普通函数任务: {task_id} ({task_name})")
        return task_id

    async def remove_task(self, task_id: str) -> bool:
        """
        移除任务

        Args:
            task_id: 任务ID

        Returns:
            是否移除成功
        """
        success = await self.scheduler.remove_task(task_id)
        if success:
            self.logger.info(f"已移除任务: {task_id}")

            # 清理相关数据
            if task_id in self.task_manager.task_execution_history:
                del self.task_manager.task_execution_history[task_id]
            if task_id in self.task_manager.task_execution_info:
                del self.task_manager.task_execution_info[task_id]
            if task_id in self.task_manager.task_priorities:
                del self.task_manager.task_priorities[task_id]
            if task_id in self.task_manager.task_dependencies:
                del self.task_manager.task_dependencies[task_id]
            if task_id in self.task_manager.task_locks:
                del self.task_manager.task_locks[task_id]

        return success

    async def run_task(self, task_id: str) -> bool:
        """
        立即运行任务

        Args:
            task_id: 任务ID

        Returns:
            是否运行成功
        """
        success = await self.scheduler.run_task(task_id)
        if success:
            self.logger.info(f"已立即运行任务: {task_id}")
        return success

    async def pause_task(self, task_id: str) -> bool:
        """
        暂停任务

        Args:
            task_id: 任务ID

        Returns:
            是否暂停成功
        """
        success = await self.scheduler.pause_task(task_id)
        if success:
            self.logger.info(f"已暂停任务: {task_id}")
        return success

    async def resume_task(self, task_id: str) -> bool:
        """
        恢复任务

        Args:
            task_id: 任务ID

        Returns:
            是否恢复成功
        """
        success = await self.scheduler.resume_task(task_id)
        if success:
            self.logger.info(f"已恢复任务: {task_id}")
        return success

    async def get_task_status(self, task_id: str) -> Optional[str]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态
        """
        return self.scheduler.get_task_status(task_id)

    async def get_all_tasks(self) -> Dict[str, Any]:
        """
        获取所有任务

        Returns:
            所有任务的状态和配置
        """
        return self.scheduler.get_all_tasks()

    async def get_task_execution_info(
        self, task_id: str
    ) -> Optional[TaskExecutionInfo]:
        """
        获取任务执行信息

        Args:
            task_id: 任务ID

        Returns:
            任务执行信息
        """
        return self.task_manager.task_execution_info.get(task_id)

    async def get_task_execution_history(
        self, task_id: str
    ) -> Optional[List[TaskExecutionInfo]]:
        """
        获取任务执行历史

        Args:
            task_id: 任务ID

        Returns:
            任务执行历史
        """
        return self.task_manager.task_execution_history.get(task_id)

    def register_task_function(self, function: Callable) -> None:
        """
        注册任务函数

        Args:
            function: 任务函数
        """
        self.scheduler.register_task_function(function)
        self.logger.info(f"已注册任务函数: {function.__name__}")

    def get_registered_functions(self) -> Dict[str, Callable]:
        """
        获取已注册的任务函数

        Returns:
            已注册的任务函数
        """
        return self.scheduler.get_registered_functions()
