"""策略分析API"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.auth import get_current_user_id
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
        info = strategy_service.get_strategy_info(strategy_name)
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
    try:
        result = strategy_service.compare(
            strategy_names=request.strategy_names,
            stock_code=request.stock_code,
            start_date=request.start_date,
            end_date=request.end_date,
            **request.strategy_params,
        )
        return StrategyCompareResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"策略比较失败: {str(e)}",
        )
