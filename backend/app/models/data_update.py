"""数据更新配置模型"""

from pydantic import BaseModel
from typing import Optional


class DataUpdateConfig(BaseModel):
    """数据更新配置"""
    auto_update_enabled: bool = False
    daily_update_hour: int = 15
    daily_update_minute: int = 30
    stock_list_update_enabled: bool = False
    stock_list_update_hour: int = 9
    stock_list_update_minute: int = 0


class DataUpdateConfigUpdate(BaseModel):
    """数据更新配置更新请求"""
    auto_update_enabled: Optional[bool] = None
    daily_update_hour: Optional[int] = None
    daily_update_minute: Optional[int] = None
    stock_list_update_enabled: Optional[bool] = None
    stock_list_update_hour: Optional[int] = None
    stock_list_update_minute: Optional[int] = None


class ManualUpdateRequest(BaseModel):
    """手动更新请求"""
    update_type: str  # 'stock_list' | 'daily_data' | 'all'
    market: Optional[str] = None  # 仅用于 daily_data
    stock_codes: Optional[list[str]] = None  # 仅用于 daily_data


class UpdateTaskStatus(BaseModel):
    """更新任务状态"""
    task_id: str
    status: str  # 'pending' | 'running' | 'completed' | 'failed'
    message: str
    progress: Optional[int] = None  # 0-100
    total: Optional[int] = None
    completed: Optional[int] = None
