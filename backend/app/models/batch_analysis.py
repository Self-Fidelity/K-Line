"""批量分析相关模型"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class BatchBuySignalRequest(BaseModel):
    """批量买点检测请求模型"""
    stock_codes: List[str]  # 股票代码列表
    strategy_names: List[str]  # 策略名称列表
    strategy_params: Dict[str, Dict[str, Any]] = {}  # 策略参数（key为策略名称，value为该策略的参数）


class StrategyBuySignal(BaseModel):
    """策略买点信号"""
    strategy_name: str
    has_buy_signal: bool  # 是否有买入信号
    latest_signal_date: Optional[str] = None  # 最新信号日期
    signal_type: Optional[str] = None  # 信号类型：'买入'、'卖出'、'持有'
    error: Optional[str] = None  # 错误信息


class StockBuySignalResult(BaseModel):
    """股票买点检测结果"""
    stock_code: str
    stock_name: Optional[str] = None
    success: bool = True  # 是否分析成功
    error: Optional[str] = None  # 错误信息
    has_buy_signal: bool = False  # 是否有任何策略产生买入信号
    strategy_signals: List[StrategyBuySignal] = []  # 各策略的信号结果
    recommended: bool = False  # 是否推荐（有买入信号）


class BatchBuySignalResponse(BaseModel):
    """批量买点检测响应模型"""
    total_count: int  # 总股票数
    success_count: int  # 成功分析数
    failed_count: int  # 失败数
    recommended_count: int  # 有买点的股票数
    results: List[StockBuySignalResult]  # 检测结果列表
    recommended_stocks: List[StockBuySignalResult]  # 有买点的股票列表
