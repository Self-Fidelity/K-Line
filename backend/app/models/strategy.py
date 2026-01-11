"""策略相关模型"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class StrategyInfo(BaseModel):
    """策略信息模型"""
    name: str
    description: str
    detailed_description: str = ""
    parameter_descriptions: Dict[str, str] = {}
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


class StrategyAnalyzeResponse(BaseModel):
    """策略分析响应模型"""
    strategy_name: str
    stock_code: str
    start_date: Optional[str]
    end_date: Optional[str]
    result: List[Dict]
    statistics: Dict


class StrategyCompareResponse(BaseModel):
    """策略比较响应模型"""
    stock_code: str
    start_date: Optional[str]
    end_date: Optional[str]
    results: List[Dict]
