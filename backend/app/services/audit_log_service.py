import sqlite3
from typing import List
from datetime import datetime, timezone
from backend.app.config import settings
from backend.app.models.audit_log import AuditLogCreate, AuditLogInfo

class AuditLogService:
    def _get_connection(self):
        conn = sqlite3.connect(settings.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def create_table_if_not_exists(self):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def log_event(self, log_data: AuditLogCreate):
        """记录审计日志"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            created_at = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                INSERT INTO audit_logs (user_id, username, action, details, ip_address, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                log_data.user_id,
                log_data.username,
                log_data.action,
                log_data.details,
                log_data.ip_address,
                created_at
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_recent_logs(self, limit: int = 20) -> List[AuditLogInfo]:
        """获取最近的日志"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, username, action, details, ip_address, created_at
                FROM audit_logs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            logs = []
            for row in cursor.fetchall():
                logs.append(AuditLogInfo(
                    id=row['id'],
                    user_id=row['user_id'],
                    username=row['username'],
                    action=row['action'],
                    details=row['details'],
                    ip_address=row['ip_address'],
                    created_at=row['created_at']
                ))
            return logs
        finally:
            conn.close()
