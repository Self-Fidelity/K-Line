"""参数集相关的Pydantic模型"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ParamSetBase(BaseModel):
    """参数集基础模型"""
    stock_code: str
    strategy_name: str
    name: str
    description: str = ""
    params: Dict[str, Any]
    param_ranges: Optional[Dict[str, List[float]]] = None
    target_metric: Optional[str] = None
    best_score: Optional[float] = None
    optimization_method: Optional[str] = None
    num_particles: Optional[int] = None
    max_iter: Optional[int] = None
    date_range: Optional[str] = None
    is_default: bool = False


class ParamSetCreate(ParamSetBase):
    """创建参数集请求"""
    pass


class ParamSetResponse(ParamSetBase):
    """参数集响应"""
    id: int
    created_at: str

    class Config:
        from_attributes = True


class ParamSetListResponse(BaseModel):
    """参数集列表响应"""
    param_sets: List[ParamSetResponse]
    total: int


class SetDefaultRequest(BaseModel):
    """设置默认参数集请求"""
    stock_code: str
    strategy_name: str
