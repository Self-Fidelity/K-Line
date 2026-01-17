from typing import Annotated
from fastapi import APIRouter, Depends, Query
from backend.app.api.auth import get_current_user_id
from backend.app.services.audit_log_service import AuditLogService
from backend.app.models.audit_log import AuditLogListResponse

router = APIRouter()
service = AuditLogService()

# Ensure table exists
service.create_table_if_not_exists()

@router.get("", response_model=AuditLogListResponse)
async def get_logs(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    limit: int = Query(20, ge=1, le=100)
):
    """获取系统日志"""
    logs = service.get_recent_logs(limit)
    return AuditLogListResponse(logs=logs, total=len(logs))
