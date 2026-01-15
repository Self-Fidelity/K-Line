"""数据获取API"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlite3 import Connection
import pandas as pd

from backend.app.dependencies import get_db
from backend.app.api.auth import get_current_user_id, get_current_admin_user
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
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """
    获取股票列表（普通用户只能从数据库读取）
    
    注意：refresh 参数已移除，普通用户只能读取数据库中的数据
    管理员请使用 /api/data/admin/refresh-stock-list 来更新股票列表
    """
    try:
        # 普通用户只能从数据库读取，不使用 force_from_api
        df = data_service.get_stock_list(market=market, force_from_api=False)
        
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
        df = data_service.get_stock_list(force_from_api=False)
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


@router.get("/stocks/{stock_code}/chip-distribution")
async def get_chip_distribution(
    stock_code: str,
    days: int = 120,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """
    获取筹码分布数据 (CYQ)
    """
    try:
        result = data_service.calculate_chip_distribution(stock_code, days=days)
        if not result:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="无法计算筹码分布（可能缺少数据）",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"计算筹码分布失败: {str(e)}",
        )
@router.post("/fetch", response_model=FetchDataResponse)
async def fetch_data(
    request: FetchDataRequest,
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
):
    """
    触发数据获取（仅管理员可用）
    
    注意：此接口需要管理员权限，用于从 akshare 获取单只股票的数据
    """
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


# ==================== 管理员专用 API ====================

@router.post("/admin/refresh-stock-list", response_model=StockListResponse)
async def refresh_stock_list(
    market: str = "all",
    current_admin: Annotated[dict, Depends(get_current_admin_user)] = None,
):
    """
    刷新股票列表（仅管理员可用）
    
    从 akshare API 获取最新的股票列表并更新到数据库
    """
    try:
        # 强制从 API 获取
        df = data_service.get_stock_list(market=market, force_from_api=True)
        
        stocks = []
        for _, row in df.iterrows():
            stocks.append(StockInfo(
                code=row["code"],
                name=row["name"],
                market=row.get("market", "other"),
                latest_date=row.get("latest_date"),
            ))
        
        return StockListResponse(
            stocks=stocks, 
            total=len(stocks),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新股票列表失败: {str(e)}",
        )


@router.post("/admin/batch-update-stocks")
async def batch_update_stocks(
    stock_codes: Optional[list[str]] = None,
    market: Optional[str] = None,
    current_admin: Annotated[dict, Depends(get_current_admin_user)] = None,
):
    """
    批量更新股票数据（仅管理员可用）
    
    如果 stock_codes 为空，则更新指定市场（market）的所有股票
    如果 market 也为空，则更新所有股票
    """
    try:
        # 获取要更新的股票列表
        if stock_codes:
            codes = stock_codes
        else:
            df = data_service.get_stock_list(market=market or "all", force_from_api=False)
            codes = df["code"].tolist()
        
        results = []
        for code in codes:
            try:
                task_id = data_service.fetch_stock_data(code)
                results.append({"code": code, "status": "success", "task_id": task_id})
            except Exception as e:
                results.append({"code": code, "status": "failed", "error": str(e)})
        
        success_count = len([r for r in results if r["status"] == "success"])
        return {
            "message": f"批量更新任务已启动，共 {len(codes)} 只股票",
            "total": len(codes),
            "success": success_count,
            "failed": len(codes) - success_count,
            "results": results,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新失败: {str(e)}",
        )
