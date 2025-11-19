"""
任务执行器和任务管理功能
提供任务执行、管理和监控的高级接口
"""

import asyncio
import inspect
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from kg.core.config import (SchedulerConfig, SchedulerConfigManager,
                            TaskConfig, scheduler_config,
                            scheduler_config_manager)

from .async_scheduler import AsyncTaskScheduler, TaskStatus


class TaskPriority(Enum):
    """任务优先级枚举"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskExecutionInfo:
    """任务执行信息"""

    task_id: str
    task_name: str
    status: TaskStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # 执行时长(秒)
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    next_run_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换日期时间为字符串
        if self.start_time:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        if self.next_run_time:
            data["next_run_time"] = self.next_run_time.isoformat()
        # 转换枚举为字符串
        data["status"] = self.status.value
        return data


class TaskManager:
    """任务管理器"""

    def __init__(self, scheduler: AsyncTaskScheduler):
        """
        初始化任务管理器

        Args:
            scheduler: 异步任务调度器实例
        """
        self.scheduler = scheduler
        self.config_manager = scheduler.config_manager
        self.task_execution_history: Dict[str, List[TaskExecutionInfo]] = {}
        self.task_execution_info: Dict[str, TaskExecutionInfo] = {}
        self.task_priorities: Dict[str, TaskPriority] = {}
        self.task_dependencies: Dict[str, List[str]] = {}
        self.task_locks: Dict[str, asyncio.Lock] = {}
        self.logger = scheduler.logger

        # 添加事件监听器
        self.scheduler.add_event_listener("job_executed", self._on_job_executed)
        self.scheduler.add_event_listener("job_error", self._on_job_error)
        self.scheduler.add_event_listener("job_missed", self._on_job_missed)

    async def create_task(
        self,
        name: str,
        function_path: str,
        cron_expression: Optional[str] = None,
        trigger_mode: str = "cron",
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        description: str = "",
        enabled: bool = True,
        max_instances: int = 1,
        timeout: Optional[int] = None,
        retry_count: int = 0,
        retry_delay: int = 60,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        depends_on: Optional[List[str]] = None,
    ) -> str:
        """
        创建并添加任务

        Args:
            name: 任务名称
            function_path: 任务函数路径
            cron_expression: Cron表达式
            trigger_mode: 触发模式
            args: 位置参数
            kwargs: 关键字参数
            description: 任务描述
            enabled: 是否启用
            max_instances: 最大并发实例数
            timeout: 超时时间(秒)
            retry_count: 重试次数
            retry_delay: 重试延迟(秒)
            tags: 任务标签
            metadata: 任务元数据
            priority: 任务优先级
            start_date: 开始时间
            end_date: 结束时间
            depends_on: 依赖的任务ID列表

        Returns:
            任务ID
        """
        # 生成任务ID
        task_id = f"task_{int(time.time())}_{name.replace(' ', '_')}"

        # 创建任务配置
        task_config = TaskConfig(
            task_id=task_id,
            task_name=name,
            task_type=trigger_mode or "cron",
            task_function=function_path,
            task_params={"args": args or [], "kwargs": kwargs or {}},
            task_trigger={
                "type": "cron",
                "expression": cron_expression or "",
                "start_date": start_date,
                "end_date": end_date,
            },
            task_dependencies=depends_on or [],
            task_priority=priority.value,
            task_active=enabled,
            task_description=description,
            max_instances=max_instances,
            timeout=timeout,
            retry_count=retry_count,
            retry_delay=retry_delay,
            task_metadata={"tags": tags or [], "metadata": metadata or {}},
        )

        # 设置任务优先级
        self.task_priorities[task_id] = priority

        # 设置任务依赖
        if depends_on:
            self.task_dependencies[task_id] = depends_on

        # 添加任务到调度器
        success = await self.scheduler.add_task(task_config)
        if not success:
            raise ValueError(f"添加任务失败: {task_id}")

        # 初始化任务执行信息
        self.task_execution_info[task_id] = TaskExecutionInfo(
            task_id=task_id, task_name=name, status=TaskStatus.PENDING
        )

        # 初始化任务执行历史
        if task_id not in self.task_execution_history:
            self.task_execution_history[task_id] = []

        # 创建任务锁
        self.task_locks[task_id] = asyncio.Lock()

        self.logger.info(f"已创建任务: {task_id} ({name})")
        return task_id

    async def update_task(self, task_id: str, **kwargs) -> bool:
        """
        更新任务

        Args:
            task_id: 任务ID
            **kwargs: 更新的字段

        Returns:
            是否更新成功
        """
        # 获取任务配置
        task_config = self.config_manager.get_task_config(task_id)
        if not task_config:
            self.logger.error(f"任务不存在: {task_id}")
            return False

        # 更新配置
        for key, value in kwargs.items():
            if hasattr(task_config, key):
                setattr(task_config, key, value)

        # 保存配置
        self.config_manager.update_task(task_id, **kwargs)

        # 移除旧任务
        await self.scheduler.remove_task(task_id)

        # 添加新任务
        success = await self.scheduler.add_task(task_config)
        if not success:
            self.logger.error(f"更新任务失败: {task_id}")
            return False

        self.logger.info(f"已更新任务: {task_id}")
        return True

    async def remove_task(self, task_id: str) -> bool:
        """
        移除任务

        Args:
            task_id: 任务ID

        Returns:
            是否移除成功
        """
        # 移除任务
        success = await self.scheduler.remove_task(task_id)
        if not success:
            return False

        # 清理任务信息
        if task_id in self.task_execution_info:
            del self.task_execution_info[task_id]

        if task_id in self.task_priorities:
            del self.task_priorities[task_id]

        if task_id in self.task_dependencies:
            del self.task_dependencies[task_id]

        if task_id in self.task_locks:
            del self.task_locks[task_id]

        self.logger.info(f"已移除任务: {task_id}")
        return True

    async def execute_task(
        self,
        task_id: str,
        wait_for_completion: bool = False,
        timeout: Optional[int] = None,
    ) -> Union[Any, bool]:
        """
        执行任务

        Args:
            task_id: 任务ID
            wait_for_completion: 是否等待执行完成
            timeout: 超时时间(秒)

        Returns:
            如果wait_for_completion为True，返回任务结果；否则返回是否成功执行
        """
        # 检查任务依赖
        if not await self._check_task_dependencies(task_id):
            self.logger.error(f"任务 {task_id} 的依赖未满足，无法执行")
            return False if not wait_for_completion else None

        # 立即执行任务
        success = await self.scheduler.run_task_now(task_id)
        if not success:
            return False if not wait_for_completion else None

        # 如果需要等待执行完成
        if wait_for_completion:
            return await self._wait_for_task_completion(task_id, timeout)

        return True

    async def pause_task(self, task_id: str) -> bool:
        """
        暂停任务

        Args:
            task_id: 任务ID

        Returns:
            是否暂停成功
        """
        return await self.scheduler.pause_task(task_id)

    async def resume_task(self, task_id: str) -> bool:
        """
        恢复任务

        Args:
            task_id: 任务ID

        Returns:
            是否恢复成功
        """
        return await self.scheduler.resume_task(task_id)

    async def enable_task(self, task_id: str) -> bool:
        """
        启用任务

        Args:
            task_id: 任务ID

        Returns:
            是否启用成功
        """
        # 更新配置
        success = self.config_manager.enable_task(task_id)
        if not success:
            return False

        # 重新加载任务
        await self.scheduler.reload_config()
        return True

    async def disable_task(self, task_id: str) -> bool:
        """
        禁用任务

        Args:
            task_id: 任务ID

        Returns:
            是否禁用成功
        """
        # 更新配置
        success = self.config_manager.disable_task(task_id)
        if not success:
            return False

        # 重新加载任务
        await self.scheduler.reload_config()
        return True

    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典
        """
        # 获取任务配置
        task_config = self.config_manager.get_task_config(task_id)
        if not task_config:
            return None

        # 获取任务状态
        status = self.scheduler.get_task_status(task_id)

        # 获取任务执行信息
        execution_info = self.task_execution_info.get(task_id)

        # 获取任务优先级
        priority = self.task_priorities.get(task_id, TaskPriority.NORMAL)

        # 获取任务依赖
        dependencies = self.task_dependencies.get(task_id, [])

        # 获取任务历史
        history = self.task_execution_history.get(task_id, [])

        # 组装任务信息
        info = {
            "id": task_config.id,
            "name": task_config.name,
            "description": task_config.description,
            "cron_expression": task_config.cron_expression,
            "enabled": task_config.enabled,
            "max_instances": task_config.max_instances,
            "timeout": task_config.timeout,
            "retry_count": task_config.retry_count,
            "retry_delay": task_config.retry_delay,
            "tags": task_config.tags,
            "metadata": task_config.metadata,
            "function_path": task_config.function_path,
            "args": task_config.args,
            "kwargs": task_config.kwargs,
            "start_date": (
                task_config.start_date.isoformat() if task_config.start_date else None
            ),
            "end_date": (
                task_config.end_date.isoformat() if task_config.end_date else None
            ),
            "depends_on": task_config.depends_on,
            "trigger_mode": task_config.trigger_mode,
            "status": status.value if status else None,
            "priority": priority.value,
            "dependencies": dependencies,
            "execution_info": execution_info.to_dict() if execution_info else None,
            "execution_history": [
                info.to_dict() for info in history[-10:]
            ],  # 最近10次执行记录
        }

        return info

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        获取所有任务信息

        Returns:
            任务信息列表
        """
        tasks = []
        for task_id in self.config_manager.get_all_tasks():
            task_info = self.get_task_info(task_id)
            if task_info:
                tasks.append(task_info)

        return tasks

    def get_tasks_by_status(self, status: TaskStatus) -> List[Dict[str, Any]]:
        """
        根据状态获取任务

        Args:
            status: 任务状态

        Returns:
            任务信息列表
        """
        tasks = []
        for task_id, task_status in self.scheduler.get_all_task_status().items():
            if task_status == status:
                task_info = self.get_task_info(task_id)
                if task_info:
                    tasks.append(task_info)

        return tasks

    def get_tasks_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        根据标签获取任务

        Args:
            tag: 标签

        Returns:
            任务信息列表
        """
        tasks = []
        for task_id, task_config in self.config_manager.get_tasks_by_tag(tag).items():
            task_info = self.get_task_info(task_id)
            if task_info:
                tasks.append(task_info)

        return tasks

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Dict[str, Any]]:
        """
        根据优先级获取任务

        Args:
            priority: 任务优先级

        Returns:
            任务信息列表
        """
        tasks = []
        for task_id, task_priority in self.task_priorities.items():
            if task_priority == priority:
                task_info = self.get_task_info(task_id)
                if task_info:
                    tasks.append(task_info)

        return tasks

    async def execute_task_chain(
        self,
        task_ids: List[str],
        stop_on_error: bool = True,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        执行任务链

        Args:
            task_ids: 任务ID列表
            stop_on_error: 是否在出错时停止
            timeout: 每个任务的超时时间(秒)

        Returns:
            执行结果字典
        """
        results = {}

        for task_id in task_ids:
            try:
                self.logger.info(f"执行任务链中的任务: {task_id}")
                result = await self.execute_task(
                    task_id, wait_for_completion=True, timeout=timeout
                )
                results[task_id] = {"success": True, "result": result}
            except Exception as e:
                self.logger.error(f"任务 {task_id} 执行失败: {e}")
                results[task_id] = {"success": False, "error": str(e)}

                if stop_on_error:
                    break

        return results

    async def _check_task_dependencies(self, task_id: str) -> bool:
        """
        检查任务依赖是否满足

        Args:
            task_id: 任务ID

        Returns:
            依赖是否满足
        """
        dependencies = self.task_dependencies.get(task_id, [])

        for dep_id in dependencies:
            dep_status = self.scheduler.get_task_status(dep_id)
            if dep_status != TaskStatus.SUCCESS:
                self.logger.warning(
                    f"任务 {task_id} 的依赖 {dep_id} 未完成，状态: {dep_status}"
                )
                return False

        return True

    async def _wait_for_task_completion(
        self, task_id: str, timeout: Optional[int] = None
    ) -> Any:
        """
        等待任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间(秒)

        Returns:
            任务执行结果
        """
        start_time = time.time()

        while True:
            status = self.scheduler.get_task_status(task_id)

            if status == TaskStatus.SUCCESS:
                return self.scheduler.get_task_result(task_id)
            elif status == TaskStatus.ERROR:
                error = self.scheduler.get_task_error(task_id)
                raise error if error else Exception("任务执行失败")

            # 检查超时
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"等待任务 {task_id} 完成超时")

            # 短暂等待
            await asyncio.sleep(0.5)

    def _on_job_executed(self, event) -> None:
        """任务执行完成事件处理"""
        task_id = event.job_id
        result = self.scheduler.get_task_result(task_id)

        # 更新执行信息
        if task_id in self.task_execution_info:
            execution_info = self.task_execution_info[task_id]
            execution_info.status = TaskStatus.SUCCESS
            execution_info.end_time = datetime.now()
            execution_info.result = result

            if execution_info.start_time:
                execution_info.duration = (
                    execution_info.end_time - execution_info.start_time
                ).total_seconds()

            # 添加到历史记录
            if task_id in self.task_execution_history:
                self.task_execution_history[task_id].append(execution_info)
                # 保留最近20次执行记录
                if len(self.task_execution_history[task_id]) > 20:
                    self.task_execution_history[task_id] = self.task_execution_history[
                        task_id
                    ][-20:]

    def _on_job_error(self, event) -> None:
        """任务执行错误事件处理"""
        task_id = event.job_id
        error = self.scheduler.get_task_error(task_id)

        # 更新执行信息
        if task_id in self.task_execution_info:
            execution_info = self.task_execution_info[task_id]
            execution_info.status = TaskStatus.ERROR
            execution_info.end_time = datetime.now()
            execution_info.error = str(error) if error else "未知错误"

            if execution_info.start_time:
                execution_info.duration = (
                    execution_info.end_time - execution_info.start_time
                ).total_seconds()

            # 添加到历史记录
            if task_id in self.task_execution_history:
                self.task_execution_history[task_id].append(execution_info)
                # 保留最近20次执行记录
                if len(self.task_execution_history[task_id]) > 20:
                    self.task_execution_history[task_id] = self.task_execution_history[
                        task_id
                    ][-20:]

    def _on_job_missed(self, event) -> None:
        """任务错过执行事件处理"""
        task_id = event.job_id

        # 更新执行信息
        if task_id in self.task_execution_info:
            execution_info = self.task_execution_info[task_id]
            execution_info.status = TaskStatus.MISSED

            # 添加到历史记录
            if task_id in self.task_execution_history:
                self.task_execution_history[task_id].append(execution_info)
                # 保留最近20次执行记录
                if len(self.task_execution_history[task_id]) > 20:
                    self.task_execution_history[task_id] = self.task_execution_history[
                        task_id
                    ][-20:]


class TaskExecutor:
    """任务执行器"""

    def __init__(self, task_manager: TaskManager):
        """
        初始化任务执行器

        Args:
            task_manager: 任务管理器实例
        """
        self.task_manager = task_manager
        self.scheduler = task_manager.scheduler
        self.logger = self.scheduler.logger

    async def execute_function(
        self,
        func: Callable,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Any:
        """
        执行函数

        Args:
            func: 函数对象
            args: 位置参数
            kwargs: 关键字参数
            timeout: 超时时间(秒)

        Returns:
            函数执行结果
        """
        args = args or []
        kwargs = kwargs or {}

        try:
            if asyncio.iscoroutinefunction(func):
                # 异步函数
                if timeout:
                    return await asyncio.wait_for(
                        func(*args, **kwargs), timeout=timeout
                    )
                else:
                    return await func(*args, **kwargs)
            else:
                # 同步函数，在线程池中执行
                loop = asyncio.get_event_loop()
                if timeout:
                    return await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: func(*args, **kwargs)),
                        timeout=timeout,
                    )
                else:
                    return await loop.run_in_executor(
                        None, lambda: func(*args, **kwargs)
                    )
        except Exception as e:
            self.logger.error(f"执行函数失败: {e}")
            raise

    async def execute_with_retry(
        self,
        func: Callable,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        timeout: Optional[int] = None,
    ) -> Any:
        """
        带重试的函数执行

        Args:
            func: 函数对象
            args: 位置参数
            kwargs: 关键字参数
            retry_count: 重试次数
            retry_delay: 重试延迟(秒)
            backoff_factor: 退避因子
            timeout: 每次执行的超时时间(秒)

        Returns:
            函数执行结果
        """
        last_exception = None
        current_delay = retry_delay

        for attempt in range(retry_count + 1):
            try:
                return await self.execute_function(func, args, kwargs, timeout)
            except Exception as e:
                last_exception = e
                if attempt < retry_count:
                    self.logger.warning(
                        f"函数执行失败，将在 {current_delay} 秒后重试 (尝试 {attempt + 1}/{retry_count + 1}): {e}"
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
                else:
                    self.logger.error(f"函数执行失败，已达最大重试次数: {e}")

        raise last_exception

    async def execute_with_timeout(
        self,
        func: Callable,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Any:
        """
        带超时的函数执行

        Args:
            func: 函数对象
            args: 位置参数
            kwargs: 关键字参数
            timeout: 超时时间(秒)

        Returns:
            函数执行结果
        """
        try:
            return await asyncio.wait_for(
                self.execute_function(func, args, kwargs), timeout=timeout
            )
        except asyncio.TimeoutError:
            self.logger.error(f"函数执行超时: {timeout}秒")
            raise TimeoutError(f"函数执行超时: {timeout}秒")

    async def execute_batch(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrency: int = 10,
        timeout: Optional[int] = None,
    ) -> List[Any]:
        """
        批量执行任务

        Args:
            tasks: 任务列表，每个任务包含func, args, kwargs等字段
            max_concurrency: 最大并发数
            timeout: 每个任务的超时时间(秒)

        Returns:
            执行结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def execute_single_task(task):
            async with semaphore:
                func = task.get("func")
                args = task.get("args", [])
                kwargs = task.get("kwargs", {})
                return await self.execute_function(func, args, kwargs, timeout)

        return await asyncio.gather(
            *[execute_single_task(task) for task in tasks], return_exceptions=True
        )
