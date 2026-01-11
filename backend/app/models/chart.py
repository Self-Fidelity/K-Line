"""图表相关模型"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChartGenerateRequest(BaseModel):
    """图表生成请求模型"""
    stock_code: str
    stock_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    strategy_name: Optional[str] = None
    strategy_params: Dict[str, Any] = {}
    chart_type: str = "kline"  # 'kline' or 'kline_with_ma'
    ma_periods: Optional[List[int]] = None


class ChartGenerateResponse(BaseModel):
    """图表生成响应模型"""
    chart_id: str
    chart_url: str
    message: str


class ChartEmbedResponse(BaseModel):
    """图表嵌入响应模型"""
    chart_url: str
    embed_code: str
