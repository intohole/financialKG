"""
任务管理API路由
提供RESTful接口来管理任务
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from kg.core.config import scheduler_config
from kg.utils.responses import APIResponse, SuccessResponse, ErrorResponse
from kg.utils.logger import get_logger

from .task_coordinator import TaskCoordinator
from .task_manager import TaskExecutionInfo

logger = get_logger(__name__)
task_coordinator = TaskCoordinator()

router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.post("/cron", response_model=APIResponse, summary="添加定时任务")
async def add_cron_task(
    task_name: str = Query(..., description="任务名称"),
    task_function: str = Query(..., description="任务函数或路径"),
    cron_expression: str = Query(..., description="Cron表达式"),
    task_params: Optional[Dict[str, Any]] = Query(None, description="任务参数"),
    task_priority: int = Query(5, description="任务优先级"),
    task_active: bool = Query(True, description="是否激活"),
    task_description: str = Query("", description="任务描述"),
    max_retries: int = Query(0, description="最大重试次数"),
    retry_delay: int = Query(60, description="重试延迟(秒)"),
    timeout: Optional[int] = Query(None, description="超时时间(秒)"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间")
):
    """
    添加定时任务
    
    Args:
        task_name: 任务名称
        task_function: 任务函数或路径
        cron_expression: Cron表达式
        task_params: 任务参数
        task_priority: 任务优先级
        task_active: 是否激活
        task_description: 任务描述
        max_retries: 最大重试次数
        retry_delay: 重试延迟(秒)
        timeout: 超时时间(秒)
        start_date: 开始时间
        end_date: 结束时间
    """
    try:
        task_id = await task_coordinator.add_cron_task(
            task_name=task_name,
            task_function=task_function,
            cron_expression=cron_expression,
            task_params=task_params,
            task_priority=task_priority,
            task_active=task_active,
            task_description=task_description,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            start_date=start_date,
            end_date=end_date
        )
        
        return SuccessResponse(data={"task_id": task_id})
    except Exception as e:
        logger.error(f"添加定时任务失败: {e}")
        return ErrorResponse(message=f"添加任务失败: {str(e)}", status_code=500)


@router.post("/interval", response_model=APIResponse, summary="添加间隔任务")
async def add_interval_task(
    task_name: str = Query(..., description="任务名称"),
    task_function: str = Query(..., description="任务函数或路径"),
    interval: int = Query(..., description="执行间隔(秒)"),
    task_params: Optional[Dict[str, Any]] = Query(None, description="任务参数"),
    task_priority: int = Query(5, description="任务优先级"),
    task_active: bool = Query(True, description="是否激活"),
    task_description: str = Query("", description="任务描述"),
    max_retries: int = Query(0, description="最大重试次数"),
    retry_delay: int = Query(60, description="重试延迟(秒)"),
    timeout: Optional[int] = Query(None, description="超时时间(秒)"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间")
):
    """
    添加间隔任务
    
    Args:
        task_name: 任务名称
        task_function: 任务函数或路径
        interval: 执行间隔(秒)
        task_params: 任务参数
        task_priority: 任务优先级
        task_active: 是否激活
        task_description: 任务描述
        max_retries: 最大重试次数
        retry_delay: 重试延迟(秒)
        timeout: 超时时间(秒)
        start_date: 开始时间
        end_date: 结束时间
    """
    try:
        task_id = await task_coordinator.add_interval_task(
            task_name=task_name,
            task_function=task_function,
            interval=interval,
            task_params=task_params,
            task_priority=task_priority,
            task_active=task_active,
            task_description=task_description,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            start_date=start_date,
            end_date=end_date
        )
        
        return SuccessResponse(data={"task_id": task_id})
    except Exception as e:
        logger.error(f"添加间隔任务失败: {e}")
        return ErrorResponse(message=f"添加任务失败: {str(e)}", status_code=500)


@router.post("/one-time", response_model=APIResponse, summary="添加一次性任务")
async def add_one_time_task(
    task_name: str = Query(..., description="任务名称"),
    task_function: str = Query(..., description="任务函数或路径"),
    run_date: datetime = Query(..., description="执行时间"),
    task_params: Optional[Dict[str, Any]] = Query(None, description="任务参数"),
    task_priority: int = Query(5, description="任务优先级"),
    task_active: bool = Query(True, description="是否激活"),
    task_description: str = Query("", description="任务描述"),
    max_retries: int = Query(0, description="最大重试次数"),
    retry_delay: int = Query(60, description="重试延迟(秒)"),
    timeout: Optional[int] = Query(None, description="超时时间(秒)")
):
    """
    添加一次性任务
    
    Args:
        task_name: 任务名称
        task_function: 任务函数或路径
        run_date: 执行时间
        task_params: 任务参数
        task_priority: 任务优先级
        task_active: 是否激活
        task_description: 任务描述
        max_retries: 最大重试次数
        retry_delay: 重试延迟(秒)
        timeout: 超时时间(秒)
    """
    try:
        task_id = await task_coordinator.add_one_time_task(
            task_name=task_name,
            task_function=task_function,
            run_date=run_date,
            task_params=task_params,
            task_priority=task_priority,
            task_active=task_active,
            task_description=task_description,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout
        )
        
        return SuccessResponse(data={"task_id": task_id})
    except Exception as e:
        logger.error(f"添加一次性任务失败: {e}")
        return ErrorResponse(message=f"添加任务失败: {str(e)}", status_code=500)


@router.post("/function", response_model=APIResponse, summary="添加普通函数任务")
async def add_function_task(
    task_name: str = Query(..., description="任务名称"),
    task_function: str = Query(..., description="任务函数或路径"),
    task_params: Optional[Dict[str, Any]] = Query(None, description="任务参数"),
    task_priority: int = Query(5, description="任务优先级"),
    task_active: bool = Query(True, description="是否激活"),
    task_description: str = Query("", description="任务描述"),
    max_retries: int = Query(0, description="最大重试次数"),
    retry_delay: int = Query(60, description="重试延迟(秒)"),
    timeout: Optional[int] = Query(None, description="超时时间(秒)")
):
    """
    添加普通函数任务
    
    Args:
        task_name: 任务名称
        task_function: 任务函数或路径
        task_params: 任务参数
        task_priority: 任务优先级
        task_active: 是否激活
        task_description: 任务描述
        max_retries: 最大重试次数
        retry_delay: 重试延迟(秒)
        timeout: 超时时间(秒)
    """
    try:
        task_id = await task_coordinator.add_function_task(
            task_name=task_name,
            task_function=task_function,
            task_params=task_params,
            task_priority=task_priority,
            task_active=task_active,
            task_description=task_description,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout
        )
        
        return SuccessResponse(data={"task_id": task_id})
    except Exception as e:
        logger.error(f"添加普通函数任务失败: {e}")
        return ErrorResponse(message=f"添加任务失败: {str(e)}", status_code=500)


@router.delete("/{task_id}", response_model=APIResponse, summary="移除任务")
async def remove_task(task_id: str):
    """
    移除任务
    
    Args:
        task_id: 任务ID
    """
    try:
        success = await task_coordinator.remove_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在")
        return SuccessResponse(data={"success": success})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除任务失败: {e}")
        return ErrorResponse(message=f"移除任务失败: {str(e)}", status_code=500)


@router.post("/{task_id}/run", response_model=APIResponse, summary="立即运行任务")
async def run_task(task_id: str):
    """
    立即运行任务
    
    Args:
        task_id: 任务ID
    """
    try:
        success = await task_coordinator.run_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在")
        return SuccessResponse(data={"success": success})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"运行任务失败: {e}")
        return ErrorResponse(message=f"运行任务失败: {str(e)}", status_code=500)


@router.post("/{task_id}/pause", response_model=APIResponse, summary="暂停任务")
async def pause_task(task_id: str):
    """
    暂停任务
    
    Args:
        task_id: 任务ID
    """
    try:
        success = await task_coordinator.pause_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在")
        return SuccessResponse(data={"success": success})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        return ErrorResponse(message=f"暂停任务失败: {str(e)}", status_code=500)


@router.post("/{task_id}/resume", response_model=APIResponse, summary="恢复任务")
async def resume_task(task_id: str):
    """
    恢复任务
    
    Args:
        task_id: 任务ID
    """
    try:
        success = await task_coordinator.resume_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在")
        return SuccessResponse(data={"success": success})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        return ErrorResponse(message=f"恢复任务失败: {str(e)}", status_code=500)


@router.get("/{task_id}", response_model=APIResponse, summary="获取任务状态")
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
    """
    try:
        status = await task_coordinator.get_task_status(task_id)
        if status is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        return SuccessResponse(data={"status": status})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return ErrorResponse(message=f"获取任务状态失败: {str(e)}", status_code=500)


@router.get("/", response_model=APIResponse, summary="获取所有任务")
async def get_all_tasks():
    """
    获取所有任务
    """
    try:
        tasks = await task_coordinator.get_all_tasks()
        return SuccessResponse(data={"tasks": tasks})
    except Exception as e:
        logger.error(f"获取所有任务失败: {e}")
        return ErrorResponse(message=f"获取所有任务失败: {str(e)}", status_code=500)


@router.get("/{task_id}/execution/info", response_model=APIResponse, summary="获取任务执行信息")
async def get_task_execution_info(task_id: str):
    """
    获取任务执行信息
    
    Args:
        task_id: 任务ID
    """
    try:
        execution_info = await task_coordinator.get_task_execution_info(task_id)
        if execution_info is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        return SuccessResponse(data={"execution_info": execution_info})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务执行信息失败: {e}")
        return ErrorResponse(message=f"获取任务执行信息失败: {str(e)}", status_code=500)


@router.get("/{task_id}/execution/history", response_model=APIResponse, summary="获取任务执行历史")
async def get_task_execution_history(task_id: str):
    """
    获取任务执行历史
    
    Args:
        task_id: 任务ID
    """
    try:
        execution_history = await task_coordinator.get_task_execution_history(task_id)
        if execution_history is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        return SuccessResponse(data={"execution_history": execution_history})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务执行历史失败: {e}")
        return ErrorResponse(message=f"获取任务执行历史失败: {str(e)}", status_code=500)
