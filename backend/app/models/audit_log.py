from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class AuditLogCreate(BaseModel):
    user_id: Optional[int] = None
    username: str
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None

class AuditLogInfo(BaseModel):
    id: int
    user_id: Optional[int]
    username: str
    action: str
    details: Optional[str]
    ip_address: Optional[str]
    created_at: str

    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    logs: List[AuditLogInfo]
    total: int
