"""自定义策略相关模型"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class CustomStrategyCreate(BaseModel):
    """创建自定义策略请求模型"""
    name: str = Field(..., description="策略名称", min_length=1, max_length=100)
    description: str = Field(default="", description="策略描述", max_length=500)
    detailed_description: str = Field(default="", description="详细说明")
    code: str = Field(..., description="策略代码", min_length=1)
    parameter_descriptions: Dict[str, str] = Field(default_factory=dict, description="参数说明")


class CustomStrategyUpdate(BaseModel):
    """更新自定义策略请求模型"""
    name: Optional[str] = Field(None, description="策略名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="策略描述", max_length=500)
    detailed_description: Optional[str] = Field(None, description="详细说明")
    code: Optional[str] = Field(None, description="策略代码", min_length=1)
    parameter_descriptions: Optional[Dict[str, str]] = Field(None, description="参数说明")


class CustomStrategyInfo(BaseModel):
    """自定义策略信息模型"""
    id: int
    user_id: int
    username: Optional[str] = None  # 创建人用户名
    name: str
    description: str
    detailed_description: str
    parameter_descriptions: Dict[str, str]
    is_public: bool
    is_system: bool
    created_at: str
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


class CustomStrategyDetail(CustomStrategyInfo):
    """自定义策略详情模型（包含代码）"""
    code: str


class CustomStrategyListResponse(BaseModel):
    """自定义策略列表响应模型"""
    strategies: list[CustomStrategyInfo]
    total: int


class CustomStrategyValidateRequest(BaseModel):
    """策略代码验证请求模型"""
    code: str = Field(..., description="策略代码", min_length=1)
    test_data: Optional[bool] = Field(default=False, description="是否使用测试数据验证")


class CustomStrategyValidateResponse(BaseModel):
    """策略代码验证响应模型"""
    valid: bool
    errors: list[str] = Field(default_factory=list, description="错误信息列表")
    warnings: list[str] = Field(default_factory=list, description="警告信息列表")
    strategy_name: Optional[str] = None
    strategy_description: Optional[str] = None
