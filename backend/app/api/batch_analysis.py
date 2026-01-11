"""批量分析API路由"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.auth import get_current_user_id
from backend.app.models.batch_analysis import (
    BatchBuySignalRequest,
    BatchBuySignalResponse,
)
from backend.app.services.batch_analysis_service import BatchAnalysisService

router = APIRouter()


@router.post("/buy-signals", response_model=BatchBuySignalResponse)
async def check_buy_signals(
    request: BatchBuySignalRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """批量检测股票买点"""
    try:
        if not request.strategy_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="至少选择一个策略",
            )
        
        if not request.stock_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="至少输入一个股票代码",
            )
        
        service = BatchAnalysisService()
        result = service.check_buy_signals(
            stock_codes=request.stock_codes,
            strategy_names=request.strategy_names,
            strategy_params=request.strategy_params,
        )
        return BatchBuySignalResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量检测买点失败: {str(e)}",
        )
