"""数据更新管理API（仅管理员）"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from backend.app.api.auth import get_current_admin_user, get_current_user_id
from backend.app.models.data_update import (
    DataUpdateConfig,
    DataUpdateConfigUpdate,
    ManualUpdateRequest,
    UpdateTaskStatus,
)
from backend.app.services.data_update_service import DataUpdateService

router = APIRouter()
update_service = DataUpdateService()


@router.get("/config", response_model=DataUpdateConfig)
async def get_update_config(
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
):
    """获取数据更新配置"""
    try:
        config = update_service.get_config()
        return DataUpdateConfig(**config)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}",
        )


@router.put("/config", response_model=DataUpdateConfig)
async def update_update_config(
    config_update: DataUpdateConfigUpdate,
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
):
    """更新数据更新配置"""
    try:
        update_dict = config_update.model_dump(exclude_unset=True)
        update_service.update_config(update_dict)
        new_config = update_service.get_config()
        return DataUpdateConfig(**new_config)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新配置失败: {str(e)}",
        )


@router.get("/scheduler/status")
async def get_scheduler_status(
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
):
    """获取调度器状态"""
    try:
        return update_service.get_scheduler_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取调度器状态失败: {str(e)}",
        )


@router.post("/manual-update")
async def manual_update(
    request: ManualUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user_id: Annotated[int, Depends(get_current_user_id)],  # Modified to allow all users
):
    """手动触发数据更新"""
    try:
        if request.update_type == "stock_list":
            # 更新股票列表
            background_tasks.add_task(
                _update_stock_list_task,
                update_service,
            )
            return {
                "message": "股票列表更新任务已启动",
                "task_type": "stock_list",
            }
        
        elif request.update_type == "daily_data":
            # 更新日K线数据
            if request.stock_codes:
                # 更新指定股票
                background_tasks.add_task(
                    _update_daily_data_task,
                    update_service,
                    request.stock_codes,
                )
                return {
                    "message": f"日K线数据更新任务已启动（{len(request.stock_codes)} 只股票）",
                    "task_type": "daily_data",
                    "stock_count": len(request.stock_codes),
                }
            else:
                # 更新指定市场或全部
                market = request.market or "all"
                background_tasks.add_task(
                    _update_daily_data_by_market_task,
                    update_service,
                    market,
                )
                return {
                    "message": f"日K线数据更新任务已启动（市场: {market}）",
                    "task_type": "daily_data",
                    "market": market,
                }
        
        elif request.update_type == "all":
            # 更新所有数据
            background_tasks.add_task(
                _update_all_task,
                update_service,
            )
            return {
                "message": "全部数据更新任务已启动",
                "task_type": "all",
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的更新类型: {request.update_type}",
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动更新任务失败: {str(e)}",
        )


# 后台任务函数
async def _update_stock_list_task(service: DataUpdateService):
    """更新股票列表任务"""
    try:
        service.data_service.get_stock_list(market="all", force_from_api=True)
    except Exception as e:
        logger.error(f"更新股票列表失败: {e}", exc_info=True)


async def _update_daily_data_task(service: DataUpdateService, stock_codes: list[str]):
    """更新指定股票的日K线数据"""
    try:
        for code in stock_codes:
            try:
                service.data_service.fetch_stock_data(code)
            except Exception as e:
                logger.error(f"更新股票 {code} 数据失败: {e}")
    except Exception as e:
        logger.error(f"批量更新日K线数据失败: {e}", exc_info=True)


async def _update_daily_data_by_market_task(service: DataUpdateService, market: str):
    """按市场更新日K线数据"""
    try:
        df = service.data_service.get_stock_list(market=market, force_from_api=False)
        codes = df["code"].tolist()
        for code in codes:
            try:
                service.data_service.fetch_stock_data(code)
            except Exception as e:
                logger.error(f"更新股票 {code} 数据失败: {e}")
    except Exception as e:
        logger.error(f"按市场更新日K线数据失败: {e}", exc_info=True)


async def _update_all_task(service: DataUpdateService):
    """更新所有数据"""
    try:
        # 先更新股票列表
        service.data_service.get_stock_list(market="all", force_from_api=True)
        # 再更新所有股票的日K线数据
        await _update_daily_data_by_market_task(service, "all")
    except Exception as e:
        logger.error(f"更新所有数据失败: {e}", exc_info=True)


# 导入 logger
from src.utils.logger import get_logger
logger = get_logger(__name__)
