"""策略相关模型"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class StrategyInfo(BaseModel):
    """策略信息模型"""
    name: str
    description: str
    detailed_description: str = ""
    parameter_descriptions: Dict[str, str] = {}
    parameters: Dict[str, Any] = {}
    is_system: bool = True


class StrategyListResponse(BaseModel):
    """策略列表响应模型"""
    strategies: List[StrategyInfo]
    total: int


class StrategyAnalyzeRequest(BaseModel):
    """策略分析请求模型"""
    strategy_name: str
    stock_code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    strategy_params: Dict[str, Any] = {}


class StrategyCompareRequest(BaseModel):
    """策略比较请求模型"""
    strategy_names: List[str]
    stock_code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    strategy_params: Dict[str, Dict[str, Any]] = {}  # key为策略名称，value为该策略的参数


class TradeRecord(BaseModel):
    """交易记录模型"""
    date: str
    type: str  # buy, sell
    price: float
    action: Optional[str] = None
    buy_price: Optional[float] = None
    buy_date: Optional[str] = None
    profit: Optional[float] = None
    profit_rate: Optional[float] = None


class StrategyStatisticsModel(BaseModel):
    """策略统计指标模型"""
    initial_capital: float
    final_equity: float
    cumulative_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    win_rate: float
    pl_ratio: float
    total_trades: int
    benchmark_return: float
    benchmark_max_drawdown: float
    
    # 详细数据系列
    equity_curve: List[float] = []
    benchmark_curve: List[float] = []
    dates: List[str] = []
    close_prices: List[float] = []
    trades: List[TradeRecord] = []
    daily_returns: List[float] = []


class StrategyAnalyzeResponse(BaseModel):
    """策略分析响应模型"""
    strategy_name: str
    stock_code: str
    stock_name: Optional[str] = None
    start_date: Optional[str]
    end_date: Optional[str]
    result: List[Dict]
    statistics: StrategyStatisticsModel  # 使用具体的模型而不是 Dict


class StrategyCompareResponse(BaseModel):
    """策略比较响应模型"""
    stock_code: str
    start_date: Optional[str]
    end_date: Optional[str]
    results: List[Dict]
