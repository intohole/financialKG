"""
任务状态监控和日志记录模块
提供任务执行状态监控、性能指标收集和日志记录功能
"""

import asyncio
import json
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from .async_scheduler import AsyncTaskScheduler, TaskStatus
from .task_manager import TaskExecutionInfo, TaskManager


class MetricType(Enum):
    """指标类型枚举"""

    COUNTER = "counter"  # 计数器
    GAUGE = "gauge"  # 仪表盘
    HISTOGRAM = "histogram"  # 直方图
    TIMER = "timer"  # 计时器


@dataclass
class Metric:
    """指标数据类"""

    name: str
    type: MetricType
    value: Union[int, float]
    labels: Dict[str, str] = None
    timestamp: datetime = None
    description: str = ""

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["type"] = self.type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class TaskMetrics:
    """任务指标数据类"""

    task_id: str
    task_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    missed_runs: int = 0
    average_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    last_run_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    success_rate: float = 0.0
    failure_rate: float = 0.0
    runs_per_hour: float = 0.0
    last_execution_time: Optional[float] = None

    def update_success(self, duration: float) -> None:
        """更新成功执行的指标"""
        self.total_runs += 1
        self.successful_runs += 1
        self.last_run_time = datetime.now()
        self.last_success_time = datetime.now()
        self.last_execution_time = duration

        # 更新持续时间指标
        self._update_duration(duration)

        # 更新成功率
        self._update_rates()

    def update_failure(self) -> None:
        """更新失败执行的指标"""
        self.total_runs += 1
        self.failed_runs += 1
        self.last_run_time = datetime.now()
        self.last_failure_time = datetime.now()

        # 更新失败率
        self._update_rates()

    def update_missed(self) -> None:
        """更新错过执行的指标"""
        self.missed_runs += 1

        # 更新失败率
        self._update_rates()

    def _update_duration(self, duration: float) -> None:
        """更新持续时间指标"""
        if self.total_runs == 1:
            self.average_duration = duration
            self.min_duration = duration
            self.max_duration = duration
        else:
            # 计算新的平均持续时间
            self.average_duration = (
                self.average_duration * (self.total_runs - 1) + duration
            ) / self.total_runs

            # 更新最小和最大持续时间
            self.min_duration = min(self.min_duration, duration)
            self.max_duration = max(self.max_duration, duration)

    def _update_rates(self) -> None:
        """更新成功率和失败率"""
        if self.total_runs > 0:
            self.success_rate = self.successful_runs / self.total_runs
            self.failure_rate = self.failed_runs / self.total_runs

    def calculate_runs_per_hour(self, hours: int = 24) -> None:
        """计算每小时运行次数"""
        if self.last_run_time:
            start_time = self.last_run_time - timedelta(hours=hours)
            self.runs_per_hour = self.total_runs / hours

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)

        # 转换日期时间为字符串
        if self.last_run_time:
            data["last_run_time"] = self.last_run_time.isoformat()
        if self.last_success_time:
            data["last_success_time"] = self.last_success_time.isoformat()
        if self.last_failure_time:
            data["last_failure_time"] = self.last_failure_time.isoformat()

        return data


class TaskMonitor:
    """任务监控器"""

    def __init__(
        self,
        task_manager: TaskManager,
        metrics_history_size: int = 1000,
        metrics_update_interval: int = 60,
    ):
        """
        初始化任务监控器

        Args:
            task_manager: 任务管理器实例
            metrics_history_size: 指标历史记录大小
            metrics_update_interval: 指标更新间隔(秒)
        """
        self.task_manager = task_manager
        self.scheduler = task_manager.scheduler
        self.logger = self.scheduler.logger

        # 监控配置
        self.metrics_history_size = metrics_history_size
        self.metrics_update_interval = metrics_update_interval

        # 指标存储
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.custom_metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=metrics_history_size)
        )
        self.global_metrics: Dict[str, Metric] = {}

        # 监控状态
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None

        # 事件监听器
        self.event_listeners: Dict[str, List[Callable]] = {
            "task_started": [],
            "task_completed": [],
            "task_failed": [],
            "task_missed": [],
            "metrics_updated": [],
        }

        # 添加事件监听器
        self.scheduler.add_event_listener("job_executed", self._on_job_executed)
        self.scheduler.add_event_listener("job_error", self._on_job_error)
        self.scheduler.add_event_listener("job_missed", self._on_job_missed)

    async def start_monitoring(self) -> None:
        """启动监控"""
        if self.monitoring:
            self.logger.warning("监控已经在运行中")
            return

        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("任务监控已启动")

    async def stop_monitoring(self) -> None:
        """停止监控"""
        if not self.monitoring:
            self.logger.warning("监控未在运行")
            return

        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("任务监控已停止")

    async def _monitoring_loop(self) -> None:
        """监控循环"""
        while self.monitoring:
            try:
                # 更新全局指标
                await self._update_global_metrics()

                # 更新任务指标
                await self._update_task_metrics()

                # 触发指标更新事件
                await self._trigger_event("metrics_updated", self.get_all_metrics())

                # 等待下一次更新
                await asyncio.sleep(self.metrics_update_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控循环出错: {e}")
                await asyncio.sleep(self.metrics_update_interval)

    async def _update_global_metrics(self) -> None:
        """更新全局指标"""
        # 获取所有任务状态
        all_task_status = self.scheduler.get_all_task_status()

        # 计算各种状态的任务数量
        pending_count = sum(
            1 for status in all_task_status.values() if status == TaskStatus.PENDING
        )
        running_count = sum(
            1 for status in all_task_status.values() if status == TaskStatus.RUNNING
        )
        success_count = sum(
            1 for status in all_task_status.values() if status == TaskStatus.SUCCESS
        )
        error_count = sum(
            1 for status in all_task_status.values() if status == TaskStatus.ERROR
        )
        missed_count = sum(
            1 for status in all_task_status.values() if status == TaskStatus.MISSED
        )

        # 更新全局指标
        self._set_metric("tasks_total", MetricType.GAUGE, len(all_task_status))
        self._set_metric("tasks_pending", MetricType.GAUGE, pending_count)
        self._set_metric("tasks_running", MetricType.GAUGE, running_count)
        self._set_metric("tasks_success", MetricType.GAUGE, success_count)
        self._set_metric("tasks_error", MetricType.GAUGE, error_count)
        self._set_metric("tasks_missed", MetricType.GAUGE, missed_count)

        # 计算成功率
        total_finished = success_count + error_count
        if total_finished > 0:
            success_rate = success_count / total_finished
            self._set_metric("tasks_success_rate", MetricType.GAUGE, success_rate)

    async def _update_task_metrics(self) -> None:
        """更新任务指标"""
        # 获取所有任务信息
        all_tasks = self.task_manager.get_all_tasks()

        for task in all_tasks:
            task_id = task["id"]

            # 初始化任务指标（如果不存在）
            if task_id not in self.task_metrics:
                self.task_metrics[task_id] = TaskMetrics(
                    task_id=task_id, task_name=task["name"]
                )

            # 计算每小时运行次数
            self.task_metrics[task_id].calculate_runs_per_hour()

    def _set_metric(
        self,
        name: str,
        metric_type: MetricType,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
        description: str = "",
    ) -> None:
        """设置指标"""
        self.global_metrics[name] = Metric(
            name=name,
            type=metric_type,
            value=value,
            labels=labels or {},
            description=description,
        )

    def increment_metric(
        self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """增加计数器指标"""
        if (
            name in self.global_metrics
            and self.global_metrics[name].type == MetricType.COUNTER
        ):
            self.global_metrics[name].value += value
        else:
            self._set_metric(name, MetricType.COUNTER, value, labels)

    def set_gauge(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """设置仪表盘指标"""
        self._set_metric(name, MetricType.GAUGE, value, labels)

    def record_timer(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """记录计时器指标"""
        self._set_metric(name, MetricType.TIMER, value, labels)

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """记录直方图指标"""
        # 添加到历史记录
        metric = Metric(
            name=name, type=MetricType.HISTOGRAM, value=value, labels=labels or {}
        )
        self.custom_metrics[name].append(metric)

        # 更新当前值
        self._set_metric(name, MetricType.HISTOGRAM, value, labels)

    def get_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """
        获取任务指标

        Args:
            task_id: 任务ID

        Returns:
            任务指标
        """
        return self.task_metrics.get(task_id)

    def get_all_task_metrics(self) -> Dict[str, TaskMetrics]:
        """
        获取所有任务指标

        Returns:
            任务指标字典
        """
        return self.task_metrics.copy()

    def get_global_metrics(self) -> Dict[str, Metric]:
        """
        获取全局指标

        Returns:
            全局指标字典
        """
        return self.global_metrics.copy()

    def get_custom_metrics(self, name: str) -> List[Metric]:
        """
        获取自定义指标历史

        Args:
            name: 指标名称

        Returns:
            指标历史列表
        """
        return list(self.custom_metrics.get(name, []))

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        获取所有指标

        Returns:
            所有指标字典
        """
        return {
            "global": {
                name: metric.to_dict() for name, metric in self.global_metrics.items()
            },
            "tasks": {
                task_id: metrics.to_dict()
                for task_id, metrics in self.task_metrics.items()
            },
            "custom": {
                name: [m.to_dict() for m in metrics]
                for name, metrics in self.custom_metrics.items()
            },
        }

    def get_task_status_summary(self) -> Dict[str, Any]:
        """
        获取任务状态摘要

        Returns:
            任务状态摘要
        """
        all_task_status = self.scheduler.get_all_task_status()

        status_counts = defaultdict(int)
        for status in all_task_status.values():
            status_counts[status.value] += 1

        return {
            "total": len(all_task_status),
            "status_counts": dict(status_counts),
            "running_tasks": self.scheduler.get_running_tasks(),
            "pending_tasks": self.scheduler.get_pending_tasks(),
            "failed_tasks": self.scheduler.get_failed_tasks(),
        }

    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取性能报告

        Args:
            hours: 报告时间范围(小时)

        Returns:
            性能报告
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        report = {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours,
            },
            "summary": {
                "total_tasks": len(self.task_metrics),
                "total_runs": sum(
                    metrics.total_runs for metrics in self.task_metrics.values()
                ),
                "total_successes": sum(
                    metrics.successful_runs for metrics in self.task_metrics.values()
                ),
                "total_failures": sum(
                    metrics.failed_runs for metrics in self.task_metrics.values()
                ),
                "total_missed": sum(
                    metrics.missed_runs for metrics in self.task_metrics.values()
                ),
            },
            "top_tasks": {
                "most_runs": [],
                "highest_success_rate": [],
                "lowest_success_rate": [],
                "slowest_avg_duration": [],
                "fastest_avg_duration": [],
            },
            "task_details": {},
        }

        # 计算总体成功率
        total_runs = report["summary"]["total_runs"]
        total_successes = report["summary"]["total_successes"]
        if total_runs > 0:
            report["summary"]["overall_success_rate"] = total_successes / total_runs
        else:
            report["summary"]["overall_success_rate"] = 0.0

        # 收集任务详情
        task_details = []
        for task_id, metrics in self.task_metrics.items():
            if metrics.total_runs > 0:
                detail = {
                    "task_id": task_id,
                    "task_name": metrics.task_name,
                    "total_runs": metrics.total_runs,
                    "successful_runs": metrics.successful_runs,
                    "failed_runs": metrics.failed_runs,
                    "missed_runs": metrics.missed_runs,
                    "success_rate": metrics.success_rate,
                    "failure_rate": metrics.failure_rate,
                    "average_duration": metrics.average_duration,
                    "min_duration": metrics.min_duration,
                    "max_duration": metrics.max_duration,
                    "runs_per_hour": metrics.runs_per_hour,
                    "last_run_time": (
                        metrics.last_run_time.isoformat()
                        if metrics.last_run_time
                        else None
                    ),
                }
                task_details.append(detail)

        # 排序并获取前5名
        if task_details:
            # 运行次数最多的任务
            task_details.sort(key=lambda x: x["total_runs"], reverse=True)
            report["top_tasks"]["most_runs"] = task_details[:5]

            # 成功率最高的任务
            task_details.sort(key=lambda x: x["success_rate"], reverse=True)
            report["top_tasks"]["highest_success_rate"] = task_details[:5]

            # 成功率最低的任务
            report["top_tasks"]["lowest_success_rate"] = task_details[-5:]

            # 平均耗时最长的任务
            task_details.sort(key=lambda x: x["average_duration"], reverse=True)
            report["top_tasks"]["slowest_avg_duration"] = task_details[:5]

            # 平均耗时最短的任务
            task_details.sort(key=lambda x: x["average_duration"])
            report["top_tasks"]["fastest_avg_duration"] = task_details[:5]

        # 所有任务详情
        report["task_details"] = {detail["task_id"]: detail for detail in task_details}

        return report

    def export_metrics(self, format: str = "json") -> str:
        """
        导出指标

        Args:
            format: 导出格式，支持json, prometheus

        Returns:
            格式化的指标字符串
        """
        if format.lower() == "json":
            return json.dumps(self.get_all_metrics(), indent=2)
        elif format.lower() == "prometheus":
            return self._export_prometheus_format()
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def _export_prometheus_format(self) -> str:
        """导出Prometheus格式的指标"""
        lines = []

        # 导出全局指标
        for name, metric in self.global_metrics.items():
            labels_str = ""
            if metric.labels:
                labels_str = (
                    "{"
                    + ",".join([f'{k}="{v}"' for k, v in metric.labels.items()])
                    + "}"
                )

            lines.append(f"# HELP {name} {metric.description}")
            lines.append(f"# TYPE {name} {metric.type.value}")
            lines.append(f"{name}{labels_str} {metric.value}")

        # 导出任务指标
        for task_id, metrics in self.task_metrics.items():
            task_name = metrics.task_name.replace(" ", "_").replace("-", "_")

            lines.append(
                f"# HELP task_{task_name}_total_runs Total runs for task {task_name}"
            )
            lines.append(f"# TYPE task_{task_name}_total_runs counter")
            lines.append(
                f'task_{task_name}_total_runs {{task_id="{task_id}"}} {metrics.total_runs}'
            )

            lines.append(
                f"# HELP task_{task_name}_successful_runs Successful runs for task {task_name}"
            )
            lines.append(f"# TYPE task_{task_name}_successful_runs counter")
            lines.append(
                f'task_{task_name}_successful_runs {{task_id="{task_id}"}} {metrics.successful_runs}'
            )

            lines.append(
                f"# HELP task_{task_name}_failed_runs Failed runs for task {task_name}"
            )
            lines.append(f"# TYPE task_{task_name}_failed_runs counter")
            lines.append(
                f'task_{task_name}_failed_runs {{task_id="{task_id}"}} {metrics.failed_runs}'
            )

            lines.append(
                f"# HELP task_{task_name}_success_rate Success rate for task {task_name}"
            )
            lines.append(f"# TYPE task_{task_name}_success_rate gauge")
            lines.append(
                f'task_{task_name}_success_rate {{task_id="{task_id}"}} {metrics.success_rate}'
            )

            lines.append(
                f"# HELP task_{task_name}_average_duration Average duration for task {task_name}"
            )
            lines.append(f"# TYPE task_{task_name}_average_duration gauge")
            lines.append(
                f'task_{task_name}_average_duration {{task_id="{task_id}"}} {metrics.average_duration}'
            )

        return "\n".join(lines)

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

    def _on_job_executed(self, event) -> None:
        """任务执行完成事件处理"""
        task_id = event.job_id

        # 获取任务执行信息
        execution_info = self.task_manager.task_execution_info.get(task_id)
        if execution_info and execution_info.duration:
            # 更新任务指标
            if task_id not in self.task_metrics:
                self.task_metrics[task_id] = TaskMetrics(
                    task_id=task_id, task_name=execution_info.task_name
                )

            self.task_metrics[task_id].update_success(execution_info.duration)

            # 记录执行时间
            self.record_timer(f"task_execution_time_{task_id}", execution_info.duration)

            # 增加成功计数
            self.increment_metric("task_success_count", 1, {"task_id": task_id})

        # 触发任务完成事件
        asyncio.create_task(self._trigger_event("task_completed", task_id))

    def _on_job_error(self, event) -> None:
        """任务执行错误事件处理"""
        task_id = event.job_id

        # 获取任务执行信息
        execution_info = self.task_manager.task_execution_info.get(task_id)
        if execution_info:
            # 更新任务指标
            if task_id not in self.task_metrics:
                self.task_metrics[task_id] = TaskMetrics(
                    task_id=task_id, task_name=execution_info.task_name
                )

            self.task_metrics[task_id].update_failure()

            # 增加失败计数
            self.increment_metric("task_failure_count", 1, {"task_id": task_id})

        # 触发任务失败事件
        asyncio.create_task(self._trigger_event("task_failed", task_id))

    def _on_job_missed(self, event) -> None:
        """任务错过执行事件处理"""
        task_id = event.job_id

        # 获取任务执行信息
        execution_info = self.task_manager.task_execution_info.get(task_id)
        if execution_info:
            # 更新任务指标
            if task_id not in self.task_metrics:
                self.task_metrics[task_id] = TaskMetrics(
                    task_id=task_id, task_name=execution_info.task_name
                )

            self.task_metrics[task_id].update_missed()

            # 增加错过计数
            self.increment_metric("task_missed_count", 1, {"task_id": task_id})

        # 触发任务错过事件
        asyncio.create_task(self._trigger_event("task_missed", task_id))
