"""每日任务 API

查看/管理每日自动优化任务，含实时进度和邮件开关。
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.app.api.auth import get_current_admin_user
from backend.app.services.daily_task_service import daily_task_service

router = APIRouter()


class EmailToggleRequest(BaseModel):
    enabled: bool


@router.get("/daily-task/status")
async def get_daily_task_status(
    current_user=Depends(get_current_admin_user),
):
    """获取每日任务状态（含实时进度）"""
    return daily_task_service.get_status()


@router.post("/daily-task/run")
async def trigger_daily_task(
    current_user=Depends(get_current_admin_user),
):
    """手动触发每日任务"""
    result = await daily_task_service.trigger_manual()
    return result


@router.get("/daily-task/progress")
async def get_progress(
    current_user=Depends(get_current_admin_user),
):
    """获取实时优化进度（前端轮询用）"""
    return daily_task_service.batch_optimizer.progress


@router.post("/daily-task/toggle-email")
async def toggle_email(
    body: EmailToggleRequest,
    current_user=Depends(get_current_admin_user),
):
    """开关邮件通知"""
    import os
    daily_task_service._enable_email = body.enabled
    os.environ["ENABLE_EMAIL_NOTIFY"] = str(body.enabled).lower()
    return {"email_enabled": body.enabled}
