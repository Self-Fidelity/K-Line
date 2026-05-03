"""每日任务 API

查看/管理每日自动优化任务。
"""

from fastapi import APIRouter, Depends
from backend.app.api.auth import get_current_admin_user
from backend.app.services.daily_task_service import daily_task_service

router = APIRouter()


@router.get("/daily-task/status")
async def get_daily_task_status(
    current_user=Depends(get_current_admin_user),
):
    """获取每日任务运行状态"""
    return daily_task_service.get_status()


@router.post("/daily-task/run")
async def trigger_daily_task(
    current_user=Depends(get_current_admin_user),
):
    """手动触发每日任务"""
    result = await daily_task_service.trigger_manual()
    return result
