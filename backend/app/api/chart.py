"""图表API"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pathlib import Path

from backend.app.api.auth import get_current_user_id
from backend.app.models.chart import (
    ChartGenerateRequest,
    ChartGenerateResponse,
    ChartEmbedResponse,
)
from backend.app.services.chart_service import ChartService
from backend.app.services.data_service import DataService
from backend.app.services.strategy_service import StrategyService

router = APIRouter()
chart_service = ChartService()
data_service = DataService()
strategy_service = StrategyService()


@router.post("/generate", response_model=ChartGenerateResponse)
async def generate_chart(
    request: ChartGenerateRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """生成图表"""
    try:
        # 获取K线数据
        data = data_service.get_kline_data(
            stock_code=request.stock_code,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        
        if data.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"股票 {request.stock_code} 没有数据",
            )
        
        # 如果有策略，执行策略分析
        strategy_result = None
        statistics = None
        if request.strategy_name:
            try:
                result = strategy_service.analyze(
                    strategy_name=request.strategy_name,
                    stock_code=request.stock_code,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    **request.strategy_params,
                )
                # 将结果转换为DataFrame
                import pandas as pd
                strategy_result = pd.DataFrame(result["result"])
                statistics = result["statistics"]
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"策略分析失败: {str(e)}",
                )
        
        # 生成图表HTML文件
        html_path = chart_service.generate_chart_html(
            data=data,
            stock_code=request.stock_code,
            stock_name=request.stock_name,
            strategy_result=strategy_result,
            statistics=statistics,
            chart_type=request.chart_type,
            ma_periods=request.ma_periods,
        )
        
        # 生成chart_id（使用文件路径的hash）
        import hashlib
        chart_id = hashlib.md5(str(html_path).encode()).hexdigest()
        
        # 获取图表URL（使用文件名，通过静态文件服务访问）
        from pathlib import Path
        html_file = Path(html_path)
        chart_url = f"/charts/{html_file.name}"
        
        return ChartGenerateResponse(
            chart_id=chart_id,
            chart_url=chart_url,
            message="图表生成成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图表生成失败: {str(e)}",
        )


@router.get("/bokeh/{chart_id}")
async def get_bokeh_chart_url(
    chart_id: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """获取Bokeh图表URL"""
    try:
        chart_url = chart_service.get_chart_url(chart_id)
        return {"chart_id": chart_id, "chart_url": chart_url}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/embed/{chart_id}")
async def get_chart_embed_code(
    chart_id: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """获取图表嵌入代码"""
    try:
        chart_url = chart_service.get_chart_url(chart_id)
        embed_code = f'<iframe src="{chart_url}" width="100%" height="600"></iframe>'
        return ChartEmbedResponse(
            chart_url=chart_url,
            embed_code=embed_code,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
