"""策略分析API"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.auth import get_current_user_id
from typing import Dict, Any, List
from pydantic import BaseModel
from backend.app.models.strategy import (
    StrategyListResponse,
    StrategyInfo,
    StrategyAnalyzeRequest,
    StrategyAnalyzeResponse,
    StrategyCompareRequest,
    StrategyCompareResponse,
)
from backend.app.services.strategy_service import StrategyService

router = APIRouter()
strategy_service = StrategyService()

class SaveParamsRequest(BaseModel):
    stock_code: str
    strategy_name: str
    params: Dict[str, Any]

class OptimizeRequest(BaseModel):
    stock_code: str
    strategy_name: str
    start_date: str = None
    end_date: str = None
    param_ranges: Dict[str, Any]  # e.g. {"short_period": [2, 20], "long_period": [20, 100]}
    method: str = "pso"
    target_metric: str = "sharpe_ratio"
    num_particles: int = 10
    max_iter: int = 10

class OptimizeResponse(BaseModel):
    best_params: Dict[str, Any]
    best_score: float
    method: str


@router.get("/list", response_model=StrategyListResponse)
async def list_strategies(
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """获取所有可用策略列表"""
    try:
        strategies = strategy_service.list_strategies(user_id=current_user_id)
        strategy_infos = []
        for s in strategies:
            # 获取完整策略信息
            full_info = strategy_service.get_strategy_info(s["name"])
            if full_info:
                strategy_infos.append(StrategyInfo(**full_info))
            else:
                # 如果获取失败，使用基本信息
                strategy_infos.append(StrategyInfo(
                    name=s["name"],
                    description=s["description"],
                    is_system=s["is_system"],
                ))
        return StrategyListResponse(strategies=strategy_infos, total=len(strategy_infos))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略列表失败: {str(e)}",
        )


@router.get("/{strategy_name}/info", response_model=StrategyInfo)
async def get_strategy_info(
    strategy_name: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """获取策略详细信息"""
    try:
        info = strategy_service.get_strategy_info(strategy_name, user_id=current_user_id)
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略 {strategy_name} 不存在",
            )
        return StrategyInfo(**info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略信息失败: {str(e)}",
        )


@router.get("/{strategy_name}/code")
async def get_strategy_code(
    strategy_name: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """获取系统策略的代码"""
    try:
        # 先检查策略是否存在
        strategy_info = strategy_service.get_strategy_info(strategy_name, user_id=current_user_id)
        if not strategy_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略 {strategy_name} 不存在",
            )
        
        # 只有系统策略才能获取代码
        if not strategy_info.get("is_system", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"策略 {strategy_name} 不是系统策略，无法获取代码",
            )
        
        code = strategy_service.get_strategy_code(strategy_name)
        if not code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"无法获取策略 {strategy_name} 的源代码，请检查日志",
            )
        return {"code": code}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略代码失败: {str(e)}",
        )


@router.post("/analyze", response_model=StrategyAnalyzeResponse)
async def analyze_strategy(
    request: StrategyAnalyzeRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """执行策略分析"""
    try:
        result = strategy_service.analyze(
            strategy_name=request.strategy_name,
            stock_code=request.stock_code,
            start_date=request.start_date,
            end_date=request.end_date,
            user_id=current_user_id,
            **request.strategy_params,
        )
        return StrategyAnalyzeResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"策略分析失败: {str(e)}",
        )


@router.post("/compare", response_model=StrategyCompareResponse)
async def compare_strategies(
    request: StrategyCompareRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """策略比较分析"""
    try:
        result = strategy_service.compare(
            strategy_names=request.strategy_names,
            stock_code=request.stock_code,
            start_date=request.start_date,
            end_date=request.end_date,
            strategy_params=request.strategy_params,
        )
        return StrategyCompareResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"策略比较失败: {str(e)}",
        )


@router.post("/params/save")
async def save_strategy_params(
    request: SaveParamsRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """保存策略参数"""
    try:
        success = strategy_service.save_strategy_params(
            stock_code=request.stock_code,
            strategy_name=request.strategy_name,
            params=request.params
        )
        if not success:
            raise HTTPException(status_code=500, detail="保存失败")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/params/{stock_code}/{strategy_name}")
async def get_strategy_params(
    stock_code: str,
    strategy_name: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """获取策略参数"""
    try:
        params = strategy_service.get_strategy_params(stock_code, strategy_name)
        return {"params": params}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_strategy(
    request: OptimizeRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """优化策略参数"""
    try:
        result = strategy_service.optimize_strategy(
            stock_code=request.stock_code,
            strategy_name=request.strategy_name,
            start_date=request.start_date,
            end_date=request.end_date,
            param_ranges=request.param_ranges,
            method=request.method,
            target_metric=request.target_metric,
            num_particles=request.num_particles,
            max_iter=request.max_iter
        )
        return OptimizeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
