"""数据更新配置模型"""

from pydantic import BaseModel, Field
from typing import Optional


class DataUpdateConfig(BaseModel):
    """数据更新配置"""
    # 日K线数据更新
    auto_update_enabled: bool = False
    daily_update_hour: int = 19
    daily_update_minute: int = 0

    # 股票列表更新
    stock_list_update_enabled: bool = False
    stock_list_update_frequency: str = Field(default="weekly", pattern="^(weekly|daily)$")
    stock_list_update_hour: int = 6
    stock_list_update_minute: int = 0

    # 爬虫速度档位: slow=慢速(N100), normal=标准, fast=快速
    update_speed_preset: str = Field(default="slow", pattern="^(slow|normal|fast)$")

    # 批次休息设置（N100防过热）
    batch_size: int = Field(default=50, ge=10, le=500)
    batch_rest_seconds: int = Field(default=60, ge=0, le=300)

    # 股票列表更新前随机等待（秒）
    pre_update_random_wait: int = Field(default=20, ge=0, le=120)

    # 增量更新（跳过已有最新数据的股票）
    incremental_update: bool = True

    # 数据源配置
    data_source: str = Field(default="akshare", pattern="^(akshare|tushare)$")


class DataUpdateConfigUpdate(BaseModel):
    """数据更新配置更新请求（所有字段可选）"""
    auto_update_enabled: Optional[bool] = None
    daily_update_hour: Optional[int] = None
    daily_update_minute: Optional[int] = None
    stock_list_update_enabled: Optional[bool] = None
    stock_list_update_frequency: Optional[str] = None
    stock_list_update_hour: Optional[int] = None
    stock_list_update_minute: Optional[int] = None
    update_speed_preset: Optional[str] = None
    batch_size: Optional[int] = None
    batch_rest_seconds: Optional[int] = None
    pre_update_random_wait: Optional[int] = None
    incremental_update: Optional[bool] = None
    data_source: Optional[str] = None


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


class DataSourceConfig(BaseModel):
    """数据源配置"""
    data_source: str = Field(default="akshare", pattern="^(akshare|tushare)$")
    tushare_token: str = ""


class DataSourceConfigUpdate(BaseModel):
    """数据源配置更新请求"""
    data_source: Optional[str] = Field(default=None, pattern="^(akshare|tushare)$")
    tushare_token: Optional[str] = None


class DataSourceTestResult(BaseModel):
    """数据源连接测试结果"""
    success: bool
    message: str
