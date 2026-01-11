"""数据获取API"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlite3 import Connection
import pandas as pd

from backend.app.dependencies import get_db
from backend.app.api.auth import get_current_user_id
from backend.app.models.data import (
    StockListResponse,
    StockInfo,
    KlineDataRequest,
    MinuteKlineDataRequest,
    FetchDataRequest,
    FetchDataResponse,
)
from backend.app.services.data_service import DataService

router = APIRouter()
data_service = DataService()


@router.get("/stocks", response_model=StockListResponse)
async def get_stock_list(
    market: str = "main",
    refresh: bool = False,
):
    """获取股票列表"""
    try:
        df = data_service.get_stock_list(market=market, refresh=refresh)
        
        stocks = []
        for _, row in df.iterrows():
            stocks.append(StockInfo(
                code=row["code"],
                name=row["name"],
                market=row.get("market", "other"),
                latest_date=row.get("latest_date"),
            ))
        
        return StockListResponse(stocks=stocks, total=len(stocks))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取股票列表失败: {str(e)}",
        )


@router.get("/stocks/{stock_code}")
async def get_stock_info(
    stock_code: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """获取单只股票信息"""
    try:
        df = data_service.get_stock_list(refresh=False)
        stock_row = df[df["code"] == stock_code]
        if stock_row.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"股票 {stock_code} 不存在",
            )
        row = stock_row.iloc[0]
        return StockInfo(code=row["code"], name=row["name"], market=row.get("market"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取股票信息失败: {str(e)}",
        )


@router.get("/stocks/{stock_code}/kline")
async def get_kline_data(
    stock_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """获取日K线数据"""
    try:
        df = data_service.get_kline_data(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
        )
        # 将DataFrame转换为字典列表
        df = df.copy()
        if "date" in df.columns:
            df["date"] = df["date"].astype(str)
        return df.to_dict("records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取K线数据失败: {str(e)}",
        )


@router.get("/stocks/{stock_code}/minute-kline")
async def get_minute_kline_data(
    stock_code: str,
    period: str,
    start_datetime: Optional[str] = None,
    end_datetime: Optional[str] = None,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """获取分时K线数据"""
    try:
        if period not in ["1", "5", "15", "30", "60"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分时周期必须是 1, 5, 15, 30, 60 之一",
            )
        df = data_service.get_minute_kline_data(
            stock_code=stock_code,
            period=period,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        return df.to_dict("records")
    except HTTPException:
        raise
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="分时数据获取功能尚未实现",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分时K线数据失败: {str(e)}",
        )


@router.post("/fetch", response_model=FetchDataResponse)
async def fetch_data(
    request: FetchDataRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """触发数据获取（异步任务）"""
    try:
        task_id = data_service.fetch_stock_data(request.stock_code or "")
        return FetchDataResponse(
            task_id=task_id,
            message=f"数据获取任务已启动: {task_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据获取失败: {str(e)}",
        )


@router.get("/fetch/status/{task_id}")
async def get_fetch_status(
    task_id: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """查询数据获取状态"""
    # TODO: 实现任务状态查询
    return {"task_id": task_id, "status": "completed", "message": "任务已完成"}
