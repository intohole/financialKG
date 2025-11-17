"""
异步任务调度器核心类
基于APScheduler实现的异步任务调度器
"""

import asyncio
import logging
import importlib
from typing import Dict, Any, Optional, Callable, List, Union
from datetime import datetime, timedelta
from enum import Enum

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.base import BaseJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

# 导入配置管理类
from kg.core.config import scheduler_config_manager, scheduler_config
from .scheduler_config import SchedulerConfig, SchedulerConfigManager, TaskConfig


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    SUCCESS = "success"  # 执行成功
    ERROR = "error"  # 执行出错
    MISSED = "missed"  # 错过执行
    STOPPED = "stopped"  # 已停止


class AsyncTaskScheduler:
    """异步任务调度器"""
    
    def __init__(self, config_manager: Optional[SchedulerConfigManager] = None):
        """
        初始化异步任务调度器
        
        Args:
            config_manager: 配置管理器，如果为None则使用项目核心配置的实例
        """
        self.config_manager = config_manager or scheduler_config_manager
        self.scheduler_config = self.config_manager.load_config()
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.task_status: Dict[str, TaskStatus] = {}
        self.task_results: Dict[str, Any] = {}
        self.task_errors: Dict[str, Exception] = {}
        self.event_listeners: Dict[str, List[Callable]] = {
            "job_executed": [],
            "job_error": [],
            "job_missed": [],
            "job_added": [],
            "job_removed": []
        }
        self.logger = self._setup_logger()
        
        # 任务函数缓存
        self._task_functions: Dict[str, Callable] = {}
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("AsyncTaskScheduler")
        logger.setLevel(getattr(logging, self.scheduler_config.log_level))
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(self.scheduler_config.log_format)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        if self.scheduler_config.log_file:
            file_handler = logging.FileHandler(self.scheduler_config.log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        return logger
    
    async def start(self) -> None:
        """启动调度器"""
        if self.scheduler and self.scheduler.running:
            self.logger.warning("调度器已经在运行中")
            return
            
        # 调试信息：查看scheduler_config的类型和属性
        self.logger.debug(f"scheduler_config类型: {type(self.scheduler_config)}")
        self.logger.debug(f"scheduler_config属性: {dir(self.scheduler_config)}")
        self.logger.debug(f"是否有job_defaults属性: {hasattr(self.scheduler_config, 'job_defaults')}")
            
        # 创建调度器配置
        jobstores = {
            "default": self._create_job_store()
        }
        
        executors = {
            "default": self._create_executor()
        }
        
        # 确保job_defaults属性存在
        if hasattr(self.scheduler_config, 'job_defaults') and self.scheduler_config.job_defaults:
            job_defaults = {
                "coalesce": self.scheduler_config.coalesce,
                "max_instances": 1,
                "misfire_grace_time": self.scheduler_config.misfire_grace_time,
                **self.scheduler_config.job_defaults
            }
        else:
            # 如果job_defaults不存在或为空，使用默认值
            job_defaults = {
                "coalesce": self.scheduler_config.coalesce,
                "max_instances": 1,
                "misfire_grace_time": self.scheduler_config.misfire_grace_time
            }
        
        # 创建调度器
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=self.scheduler_config.timezone
        )
        
        # 添加事件监听器
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._job_missed, EVENT_JOB_MISSED)
        
        # 启动调度器
        self.scheduler.start()
        self.logger.info("异步任务调度器已启动")
        
        # 加载并添加所有启用的任务
        await self._load_enabled_tasks()
    
    async def stop(self, wait: bool = True) -> None:
        """停止调度器"""
        if not self.scheduler or not self.scheduler.running:
            self.logger.warning("调度器未在运行")
            return
            
        self.scheduler.shutdown(wait=wait)
        self.logger.info("异步任务调度器已停止")
    
    def _create_job_store(self) -> BaseJobStore:
        """创建任务存储"""
        job_store_config = self.scheduler_config.job_store
        store_type = job_store_config.get("type", "memory")
        
        if store_type == "memory":
            return MemoryJobStore()
        elif store_type == "sqlalchemy":
            from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
            url = job_store_config.get("url", "sqlite:///jobs.sqlite")
            return SQLAlchemyJobStore(url=url)
        elif store_type == "redis":
            from apscheduler.jobstores.redis import RedisJobStore
            url = job_store_config.get("url", "redis://localhost:6379/0")
            return RedisJobStore.from_url(url)
        elif store_type == "mongodb":
            from apscheduler.jobstores.mongodb import MongoDBJobStore
            url = job_store_config.get("url", "mongodb://localhost:27017/apscheduler")
            return MongoDBJobStore(url)
        else:
            raise ValueError(f"不支持的任务存储类型: {store_type}")
    
    def _create_executor(self) -> AsyncIOExecutor:
        """创建任务执行器"""
        executor_config = self.scheduler_config.executor
        executor_type = executor_config.get("type", "asyncio")
        
        if executor_type == "asyncio":
            return AsyncIOExecutor()
        else:
            raise ValueError(f"不支持的执行器类型: {executor_type}")
    
    async def _load_enabled_tasks(self) -> None:
        """加载所有启用的任务"""
        enabled_tasks = self.config_manager.get_enabled_tasks()
        
        for task_id, task_config in enabled_tasks.items():
            try:
                await self.add_task(task_config)
                self.logger.info(f"已加载任务: {task_id}")
            except Exception as e:
                self.logger.error(f"加载任务 {task_id} 失败: {e}")
    
    async def add_task(self, task_config: TaskConfig) -> bool:
        """
        添加任务
        
        Args:
            task_config: 任务配置
            
        Returns:
            是否添加成功
        """
        if not self.scheduler or not self.scheduler.running:
            self.logger.error("调度器未启动，无法添加任务")
            return False
            
        try:
            # 获取任务函数
            task_func = self._get_task_function(task_config.task_function)
            if not task_func:
                self.logger.error(f"无法获取任务函数: {task_config.task_function}")
                return False
            
            # 创建触发器
            trigger = self._create_trigger(task_config)
            
            # 添加任务
            job = self.scheduler.add_job(
                func=self._execute_task,
                trigger=trigger,
                args=[task_config, task_func],
                id=task_config.task_id,
                name=task_config.task_name,
                max_instances=task_config.max_instances,
                start_date=task_config.start_date,
                end_date=task_config.end_date,
                **task_config.metadata
            )
            
            # 更新任务状态
            self.task_status[task_config.task_id] = TaskStatus.PENDING
            
            # 触发任务添加事件
            await self._trigger_event("job_added", job)
            
            self.logger.info(f"已添加任务: {task_config.task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加任务 {task_config.task_id} 失败: {e}")
            return False
    
    async def remove_task(self, task_id: str) -> bool:
        """
        移除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否移除成功
        """
        if not self.scheduler or not self.scheduler.running:
            self.logger.error("调度器未启动，无法移除任务")
            return False
            
        try:
            # 移除任务
            self.scheduler.remove_job(task_id)
            
            # 清理任务状态
            if task_id in self.task_status:
                del self.task_status[task_id]
            if task_id in self.task_results:
                del self.task_results[task_id]
            if task_id in self.task_errors:
                del self.task_errors[task_id]
                
            # 触发任务移除事件
            await self._trigger_event("job_removed", task_id)
            
            self.logger.info(f"已移除任务: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除任务 {task_id} 失败: {e}")
            return False
    
    async def pause_task(self, task_id: str) -> bool:
        """
        暂停任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否暂停成功
        """
        if not self.scheduler or not self.scheduler.running:
            self.logger.error("调度器未启动，无法暂停任务")
            return False
            
        try:
            self.scheduler.pause_job(task_id)
            self.logger.info(f"已暂停任务: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"暂停任务 {task_id} 失败: {e}")
            return False
    
    async def resume_task(self, task_id: str) -> bool:
        """
        恢复任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否恢复成功
        """
        if not self.scheduler or not self.scheduler.running:
            self.logger.error("调度器未启动，无法恢复任务")
            return False
            
        try:
            self.scheduler.resume_job(task_id)
            self.logger.info(f"已恢复任务: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复任务 {task_id} 失败: {e}")
            return False
    
    async def run_task_now(self, task_id: str) -> bool:
        """
        立即执行任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否执行成功
        """
        if not self.scheduler or not self.scheduler.running:
            self.logger.error("调度器未启动，无法执行任务")
            return False
            
        try:
            self.scheduler.run_job(task_id)
            self.logger.info(f"已立即执行任务: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"立即执行任务 {task_id} 失败: {e}")
            return False
    
    def register_task_function(self, function: Callable) -> None:
        """
        注册任务函数
        
        Args:
            function: 任务函数对象
        """
        # 使用函数的 __name__ 作为键
        function_name = function.__name__
        self._task_functions[function_name] = function
        self.logger.info(f"已注册任务函数: {function_name}")
    
    def _get_task_function(self, function_path: str) -> Optional[Callable]:
        """
        获取任务函数
        
        Args:
            function_path: 函数路径，格式为 "module.submodule:function_name" 或直接函数名
            
        Returns:
            任务函数
        """
        # 先从缓存中查找
        if function_path in self._task_functions:
            return self._task_functions[function_path]
            
        try:
            # 尝试直接解析为模块路径和函数名
            if ":" in function_path:
                # 解析模块路径和函数名
                module_path, function_name = function_path.split(":")
                
                # 导入模块
                module = importlib.import_module(module_path)
                
                # 获取函数
                task_func = getattr(module, function_name)
                
                # 缓存函数
                self._task_functions[function_path] = task_func
                
                return task_func
            else:
                # 直接作为函数名查找
                self.logger.error(f"函数未注册: {function_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"获取任务函数失败: {function_path}, 错误: {e}")
            return None
    
    def _create_trigger(self, task_config: TaskConfig):
        """
        创建触发器
        
        Args:
            task_config: 任务配置
            
        Returns:
            触发器对象
        """
        trigger_mode = task_config.trigger_mode
        
        if trigger_mode == "date":
            # 一次性触发器
            run_date = task_config.start_date or datetime.now()
            return DateTrigger(run_date=run_date)
        elif trigger_mode == "interval":
            # 间隔触发器
            seconds = task_config.metadata.get("seconds", 0)
            minutes = task_config.metadata.get("minutes", 0)
            hours = task_config.metadata.get("hours", 0)
            days = task_config.metadata.get("days", 0)
            weeks = task_config.metadata.get("weeks", 0)
            
            return IntervalTrigger(
                seconds=seconds,
                minutes=minutes,
                hours=hours,
                days=days,
                weeks=weeks,
                start_date=task_config.start_date,
                end_date=task_config.end_date
            )
        elif trigger_mode == "cron":
            # Cron表达式触发器
            cron_expression = task_config.cron_expression
            if not cron_expression:
                raise ValueError("Cron触发器需要提供cron_expression")
                
            # 解析cron表达式
            parts = cron_expression.split()
            if len(parts) != 6:
                raise ValueError("Cron表达式格式错误，应为6个字段: 分 时 日 月 周 秒")
                
            minute, hour, day, month, day_of_week, second = parts
            
            return CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                second=second,
                start_date=task_config.start_date,
                end_date=task_config.end_date
            )
        else:
            raise ValueError(f"不支持的触发器类型: {trigger_mode}")
    
    async def _execute_task(self, task_config: TaskConfig, task_func: Callable) -> Any:
        """
        执行任务
        
        Args:
            task_config: 任务配置
            task_func: 任务函数
            
        Returns:
            任务执行结果
        """
        task_id = task_config.id
        self.task_status[task_id] = TaskStatus.RUNNING
        
        try:
            # 执行任务
            if asyncio.iscoroutinefunction(task_func):
                # 异步函数
                result = await task_func(*task_config.args, **task_config.kwargs)
            else:
                # 同步函数，在线程池中执行
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    lambda: task_func(*task_config.args, **task_config.kwargs)
                )
                
            # 更新任务状态和结果
            self.task_status[task_id] = TaskStatus.SUCCESS
            self.task_results[task_id] = result
            
            return result
            
        except Exception as e:
            # 更新任务状态和错误
            self.task_status[task_id] = TaskStatus.ERROR
            self.task_errors[task_id] = e
            
            # 重试逻辑
            if task_config.retry_count > 0:
                self.logger.warning(f"任务 {task_id} 执行失败，将在 {task_config.retry_delay} 秒后重试")
                await asyncio.sleep(task_config.retry_delay)
                
                # 创建重试任务
                retry_task_config = TaskConfig(
                    id=f"{task_id}_retry",
                    name=f"{task_config.name} (重试)",
                    description=f"{task_config.description} - 重试任务",
                    function_path=task_config.function_path,
                    args=task_config.args,
                    kwargs=task_config.kwargs,
                    retry_count=task_config.retry_count - 1,
                    retry_delay=task_config.retry_delay,
                    trigger_mode="date",
                    start_date=datetime.now() + timedelta(seconds=task_config.retry_delay)
                )
                
                await self.add_task(retry_task_config)
            
            raise e
    
    def _job_executed(self, event) -> None:
        """任务执行完成事件处理"""
        job_id = event.job_id
        self.logger.info(f"任务 {job_id} 执行完成")
        self.task_status[job_id] = TaskStatus.SUCCESS
        
        # 触发事件监听器
        asyncio.create_task(self._trigger_event("job_executed", event))
    
    def _job_error(self, event) -> None:
        """任务执行错误事件处理"""
        job_id = event.job_id
        exception = event.exception
        self.logger.error(f"任务 {job_id} 执行出错: {exception}")
        self.task_status[job_id] = TaskStatus.ERROR
        self.task_errors[job_id] = exception
        
        # 触发事件监听器
        asyncio.create_task(self._trigger_event("job_error", event))
    
    def _job_missed(self, event) -> None:
        """任务错过执行事件处理"""
        job_id = event.job_id
        self.logger.warning(f"任务 {job_id} 错过执行")
        self.task_status[job_id] = TaskStatus.MISSED
        
        # 触发事件监听器
        asyncio.create_task(self._trigger_event("job_missed", event))
    
    async def _trigger_event(self, event_name: str, event_data: Any) -> None:
        """
        触发事件监听器
        
        Args:
            event_name: 事件名称
            event_data: 事件数据
        """
        if event_name in self.event_listeners:
            for listener in self.event_listeners[event_name]:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(event_data)
                    else:
                        listener(event_data)
                except Exception as e:
                    self.logger.error(f"事件监听器执行失败: {e}")
    
    def add_event_listener(self, event_name: str, listener: Callable) -> None:
        """
        添加事件监听器
        
        Args:
            event_name: 事件名称
            listener: 监听器函数
        """
        if event_name not in self.event_listeners:
            self.event_listeners[event_name] = []
            
        self.event_listeners[event_name].append(listener)
    
    def remove_event_listener(self, event_name: str, listener: Callable) -> None:
        """
        移除事件监听器
        
        Args:
            event_name: 事件名称
            listener: 监听器函数
        """
        if event_name in self.event_listeners:
            try:
                self.event_listeners[event_name].remove(listener)
            except ValueError:
                pass
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态
        """
        return self.task_status.get(task_id)
    
    def get_task_result(self, task_id: str) -> Any:
        """
        获取任务执行结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务执行结果
        """
        return self.task_results.get(task_id)
    
    def get_task_error(self, task_id: str) -> Optional[Exception]:
        """
        获取任务执行错误
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务执行错误
        """
        return self.task_errors.get(task_id)
    
    def get_all_task_status(self) -> Dict[str, TaskStatus]:
        """
        获取所有任务状态
        
        Returns:
            任务状态字典
        """
        return self.task_status.copy()
    
    def get_running_tasks(self) -> List[str]:
        """
        获取正在运行的任务ID列表
        
        Returns:
            正在运行的任务ID列表
        """
        return [
            task_id for task_id, status in self.task_status.items()
            if status == TaskStatus.RUNNING
        ]
    
    def get_pending_tasks(self) -> List[str]:
        """
        获取等待执行的任务ID列表
        
        Returns:
            等待执行的任务ID列表
        """
        return [
            task_id for task_id, status in self.task_status.items()
            if status == TaskStatus.PENDING
        ]
    
    def get_failed_tasks(self) -> List[str]:
        """
        获取执行失败的任务ID列表
        
        Returns:
            执行失败的任务ID列表
        """
        return [
            task_id for task_id, status in self.task_status.items()
            if status == TaskStatus.ERROR
        ]
    
    async def reload_config(self) -> None:
        """重新加载配置"""
        self.config_manager.load_config()
        self.scheduler_config = self.config_manager.get_scheduler_config()
        
        # 重新设置日志
        self.logger = self._setup_logger()
        
        # 重新加载任务
        await self._load_enabled_tasks()
        
        self.logger.info("配置已重新加载")
    
    def get_scheduler_info(self) -> Dict[str, Any]:
        """
        获取调度器信息
        
        Returns:
            调度器信息字典
        """
        if not self.scheduler:
            return {"status": "stopped"}
            
        return {
            "status": "running" if self.scheduler.running else "stopped",
            "timezone": str(self.scheduler.timezone),
            "job_count": len(self.scheduler.get_jobs()),
            "state": self.scheduler.state,
            "task_status": {k: v.value for k, v in self.task_status.items()}
        }