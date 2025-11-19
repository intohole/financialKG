"""
调度服务主类
整合所有调度功能，提供统一的服务接口
"""

import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from kg.core.config import (SchedulerConfig, SchedulerConfigManager,
                            TaskConfig, scheduler_config,
                            scheduler_config_manager)

from .async_scheduler import AsyncTaskScheduler
from .task_manager import TaskManager
from .task_monitor import TaskMonitor


class SchedulerService:
    """调度服务主类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化调度服务

        Args:
            config_path: 配置文件路径，如果不提供则使用默认配置
        """
        self.config_path = config_path
        self.config_manager = SchedulerConfigManager()
        self.config: Optional[SchedulerConfig] = None

        # 核心组件
        self.scheduler: Optional[AsyncTaskScheduler] = None
        self.task_manager: Optional[TaskManager] = None
        self.monitor: Optional[TaskMonitor] = None

        # 服务状态
        self.running = False
        self.shutdown_event = asyncio.Event()

        # 信号处理
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """设置信号处理器"""
        if sys.platform != "win32":
            # Unix-like系统支持信号处理
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame) -> None:
        """信号处理器"""
        print(f"接收到信号 {signum}，准备关闭服务...")
        asyncio.create_task(self.stop())

    async def initialize(self) -> None:
        """初始化服务"""
        try:
            # 加载配置
            if self.config_path and os.path.exists(self.config_path):
                self.config = self.config_manager.load_config(self.config_path)
                print(f"从配置文件加载配置: {self.config_path}")
            else:
                # 创建默认配置对象
                from dataclasses import dataclass, field

                @dataclass
                class SchedulerSettings:
                    timezone: str = "Asia/Shanghai"
                    max_workers: int = 10
                    job_defaults: Dict[str, Any] = field(
                        default_factory=lambda: {"coalesce": False, "max_instances": 3}
                    )

                @dataclass
                class SchedulerConfig:
                    scheduler: SchedulerSettings = field(
                        default_factory=SchedulerSettings
                    )

                self.config = SchedulerConfig()
                print("使用内置默认配置")

            # 创建核心组件
            self.scheduler = AsyncTaskScheduler(self.config.scheduler)
            self.task_manager = TaskManager(self.scheduler)
            self.monitor = TaskMonitor(self.task_manager)

            print("调度服务初始化完成")
        except Exception as e:
            print(f"初始化调度服务时出错: {str(e)}")
            # 创建基本配置和组件，确保即使出错也能继续运行
            from dataclasses import dataclass, field

            @dataclass
            class SchedulerSettings:
                timezone: str = "Asia/Shanghai"
                max_workers: int = 10
                job_defaults: Dict[str, Any] = field(
                    default_factory=lambda: {"coalesce": False, "max_instances": 3}
                )

            @dataclass
            class SchedulerConfig:
                scheduler: SchedulerSettings = field(default_factory=SchedulerSettings)

            self.config = SchedulerConfig()

            # 安全初始化组件
            try:
                self.scheduler = AsyncTaskScheduler(self.config.scheduler)
                self.task_manager = TaskManager(self.scheduler)
                self.monitor = TaskMonitor(self.task_manager)
            except Exception as inner_e:
                print(f"创建核心组件时出错: {str(inner_e)}")
                # 即使组件创建失败，也要确保服务能继续运行
                pass

    async def start(self) -> None:
        """启动服务"""
        if self.running:
            print("服务已经在运行中")
            return

        if not self.config:
            await self.initialize()

        # 启动调度器
        await self.scheduler.start()
        print("调度器已启动")

        # 启动监控
        await self.monitor.start_monitoring()
        print("任务监控已启动")

        # 添加配置中的任务
        await self._load_tasks_from_config()

        self.running = True
        print("调度服务已启动")

    async def stop(self) -> None:
        """停止服务"""
        if not self.running:
            print("服务未在运行")
            return

        print("正在停止调度服务...")

        # 停止监控
        if self.monitor:
            await self.monitor.stop_monitoring()
            print("任务监控已停止")

        # 停止调度器
        if self.scheduler:
            await self.scheduler.stop()
            print("调度器已停止")

        self.running = False
        self.shutdown_event.set()
        print("调度服务已停止")

    async def _load_tasks_from_config(self) -> None:
        """从配置加载任务"""
        if not self.config or not self.config.tasks:
            return

        for task_config in self.config.tasks:
            if task_config.enabled:
                try:
                    # 注册任务函数（如果需要）
                    self._register_task_function(task_config.func)

                    # 添加任务
                    task_id = self.task_manager.add_task_from_config(task_config)
                    print(f"添加任务: {task_config.name} (ID: {task_id})")
                except Exception as e:
                    print(f"添加任务失败: {task_config.name}, 错误: {e}")

    def _register_task_function(self, func_path: str) -> None:
        """
        注册任务函数

        Args:
            func_path: 函数路径，格式为 "module.function"
        """
        # 这里可以实现动态导入和注册函数的逻辑
        # 为了简化，这里只是一个占位符
        pass

    async def add_task(
        self,
        task_id: str,
        name: str,
        func: Union[str, Callable],
        trigger: str,
        trigger_args: Dict[str, Any],
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None,
        enabled: bool = True,
        priority: str = "medium",
        max_retries: int = 3,
        retry_delay: int = 60,
        timeout: int = 300,
        description: str = "",
    ) -> str:
        """
        添加任务

        Args:
            task_id: 任务ID
            name: 任务名称
            func: 任务函数或函数路径
            trigger: 触发器类型 (date, interval, cron)
            trigger_args: 触发器参数
            args: 位置参数
            kwargs: 关键字参数
            enabled: 是否启用
            priority: 任务优先级
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            timeout: 超时时间(秒)
            description: 任务描述

        Returns:
            任务ID
        """
        if not self.task_manager:
            raise RuntimeError("服务未初始化")

        # 如果是函数对象，注册它
        if callable(func):
            self.task_manager.register_task_function(task_id, func)
            func = task_id

        # 创建任务配置
        # 已从项目核心配置导入TaskConfig
        task_config = TaskConfig(
            task_id=task_id,
            task_name=name,
            task_type=task_type or "function",
            task_function=func,
            task_params={"args": args or [], "kwargs": kwargs or {}},
            task_trigger={"type": trigger, "args": trigger_args or {}},
            task_dependencies=[],
            task_priority=priority,
            task_active=enabled,
            task_description=description,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
        )

        # 添加任务
        return self.task_manager.add_task_from_config(task_config)

    async def remove_task(self, task_id: str) -> bool:
        """
        移除任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功移除
        """
        if not self.task_manager:
            raise RuntimeError("服务未初始化")

        return await self.task_manager.remove_task(task_id)

    async def pause_task(self, task_id: str) -> bool:
        """
        暂停任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功暂停
        """
        if not self.task_manager:
            raise RuntimeError("服务未初始化")

        return await self.task_manager.pause_task(task_id)

    async def resume_task(self, task_id: str) -> bool:
        """
        恢复任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功恢复
        """
        if not self.task_manager:
            raise RuntimeError("服务未初始化")

        return await self.task_manager.resume_task(task_id)

    async def run_task_now(self, task_id: str) -> bool:
        """
        立即执行任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功触发执行
        """
        if not self.task_manager:
            raise RuntimeError("服务未初始化")

        return await self.task_manager.run_task_now(task_id)

    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态
        """
        if not self.scheduler:
            raise RuntimeError("服务未初始化")

        return self.scheduler.get_task_status(task_id)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        获取所有任务

        Returns:
            任务列表
        """
        if not self.task_manager:
            raise RuntimeError("服务未初始化")

        return self.task_manager.get_all_tasks()

    def get_task_metrics(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务指标

        Args:
            task_id: 任务ID

        Returns:
            任务指标
        """
        if not self.monitor:
            raise RuntimeError("服务未初始化")

        metrics = self.monitor.get_task_metrics(task_id)
        return metrics.to_dict() if metrics else None

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        获取所有指标

        Returns:
            所有指标
        """
        if not self.monitor:
            raise RuntimeError("服务未初始化")

        return self.monitor.get_all_metrics()

    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取性能报告

        Args:
            hours: 报告时间范围(小时)

        Returns:
            性能报告
        """
        if not self.monitor:
            raise RuntimeError("服务未初始化")

        return self.monitor.get_performance_report(hours)

    async def save_config(self, config_path: Optional[str] = None) -> None:
        """
        保存当前配置

        Args:
            config_path: 配置文件路径，如果不提供则使用初始化时的路径
        """
        if not self.config:
            raise RuntimeError("服务未初始化")

        path = config_path or self.config_path
        if not path:
            raise ValueError("未指定配置文件路径")

        # 更新配置中的任务列表
        if self.task_manager:
            all_tasks = self.task_manager.get_all_tasks()
            self.config.tasks = []

            for task in all_tasks:
                # 获取任务详细信息
                task_detail = self.task_manager.get_task(task["id"])
                if task_detail:
                    self.config.tasks.append(task_detail)

        # 保存配置
        self.config_manager.save_config(self.config, path)
        print(f"配置已保存到: {path}")

    async def reload_config(self, config_path: Optional[str] = None) -> None:
        """
        重新加载配置

        Args:
            config_path: 配置文件路径，如果不提供则使用初始化时的路径
        """
        if self.running:
            print("服务正在运行，无法重新加载配置")
            return

        path = config_path or self.config_path
        if not path or not os.path.exists(path):
            print("配置文件不存在，使用默认配置")
            self.config = self.config_manager.get_default_config()
        else:
            self.config = self.config_manager.load_config(path)
            print(f"从配置文件重新加载配置: {path}")

        # 重新初始化服务
        await self.initialize()

    async def run_forever(self) -> None:
        """持续运行服务直到收到停止信号"""
        if not self.running:
            await self.start()

        try:
            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()


class SchedulerServiceManager:
    """调度服务管理器"""

    def __init__(self):
        """初始化服务管理器"""
        self.services: Dict[str, SchedulerService] = {}

    async def create_service(
        self, service_name: str, config_path: Optional[str] = None
    ) -> SchedulerService:
        """
        创建调度服务

        Args:
            service_name: 服务名称
            config_path: 配置文件路径

        Returns:
            调度服务实例
        """
        if service_name in self.services:
            raise ValueError(f"服务 {service_name} 已存在")

        service = SchedulerService(config_path)
        await service.initialize()
        self.services[service_name] = service

        return service

    def get_service(self, service_name: str) -> Optional[SchedulerService]:
        """
        获取调度服务

        Args:
            service_name: 服务名称

        Returns:
            调度服务实例
        """
        return self.services.get(service_name)

    async def start_service(self, service_name: str) -> None:
        """
        启动服务

        Args:
            service_name: 服务名称
        """
        service = self.get_service(service_name)
        if service:
            await service.start()
        else:
            raise ValueError(f"服务 {service_name} 不存在")

    async def stop_service(self, service_name: str) -> None:
        """
        停止服务

        Args:
            service_name: 服务名称
        """
        service = self.get_service(service_name)
        if service:
            await service.stop()
        else:
            raise ValueError(f"服务 {service_name} 不存在")

    async def start_all_services(self) -> None:
        """启动所有服务"""
        for service_name, service in self.services.items():
            try:
                await service.start()
                print(f"服务 {service_name} 已启动")
            except Exception as e:
                print(f"启动服务 {service_name} 失败: {e}")

    async def stop_all_services(self) -> None:
        """停止所有服务"""
        for service_name, service in self.services.items():
            try:
                await service.stop()
                print(f"服务 {service_name} 已停止")
            except Exception as e:
                print(f"停止服务 {service_name} 失败: {e}")

    async def remove_service(self, service_name: str) -> None:
        """
        移除服务

        Args:
            service_name: 服务名称
        """
        service = self.get_service(service_name)
        if service:
            await service.stop()
            del self.services[service_name]
        else:
            raise ValueError(f"服务 {service_name} 不存在")

    def list_services(self) -> List[str]:
        """
        列出所有服务名称

        Returns:
            服务名称列表
        """
        return list(self.services.keys())

    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        获取服务状态

        Args:
            service_name: 服务名称

        Returns:
            服务状态
        """
        service = self.get_service(service_name)
        if not service:
            return None

        return {
            "name": service_name,
            "running": service.running,
            "config_path": service.config_path,
            "task_count": len(service.get_all_tasks()) if service.task_manager else 0,
        }

    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有服务状态

        Returns:
            所有服务状态
        """
        return {
            service_name: self.get_service_status(service_name)
            for service_name in self.services
        }
