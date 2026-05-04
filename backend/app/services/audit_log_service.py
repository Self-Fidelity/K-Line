from typing import List
from datetime import datetime, timezone
from backend.app.config import settings
from backend.app.models.audit_log import AuditLogCreate, AuditLogInfo
from backend.app.dependencies import get_storage


class AuditLogService:
    def __init__(self):
        self.storage = get_storage()

    def create_table_if_not_exists(self):
        """审计日志表由存储层自动初始化，此方法保留向后兼容"""
        pass

    def log_event(self, log_data: AuditLogCreate):
        """记录审计日志"""
        return self.storage.create_audit_log(
            username=log_data.username,
            action=log_data.action,
            details=log_data.details,
            ip_address=log_data.ip_address,
        )

    def get_recent_logs(self, limit: int = 20) -> List[AuditLogInfo]:
        """获取最近的日志"""
        rows = self.storage.list_audit_logs(limit=limit, offset=0)
        return [
            AuditLogInfo(
                id=row.get("id", 0),
                user_id=row.get("user_id"),
                username=row.get("username", ""),
                action=row.get("action", ""),
                details=row.get("details"),
                ip_address=row.get("ip_address"),
                created_at=row.get("created_at", ""),
            )
            for row in rows
        ]
