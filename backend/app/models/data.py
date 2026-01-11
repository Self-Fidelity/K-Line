"""数据相关模型"""

from pydantic import BaseModel
from typing import Optional, List, Dict


class StockInfo(BaseModel):
    """股票信息模型"""
    code: str
    name: str
    market: Optional[str] = None
    latest_date: Optional[str] = None  # 最新数据日期


class StockListResponse(BaseModel):
    """股票列表响应模型"""
    stocks: List[StockInfo]
    total: int


class KlineDataRequest(BaseModel):
    """K线数据请求模型"""
    stock_code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class MinuteKlineDataRequest(BaseModel):
    """分时K线数据请求模型"""
    stock_code: str
    period: str  # '1', '5', '15', '30', '60'
    start_datetime: Optional[str] = None
    end_datetime: Optional[str] = None


class FetchDataRequest(BaseModel):
    """数据获取请求模型"""
    stock_code: Optional[str] = None  # 如果为空，则获取所有非自选股票


class FetchDataResponse(BaseModel):
    """数据获取响应模型"""
    task_id: str
    message: str
