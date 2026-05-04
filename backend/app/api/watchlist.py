from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timezone

from backend.app.dependencies import get_storage
from backend.app.models.watchlist import WatchlistCreate, WatchlistResponse, WatchlistStatus
from backend.app.models.auth import UserResponse
from backend.app.api.auth import get_current_active_user

router = APIRouter()


@router.get("", response_model=List[WatchlistResponse])
async def get_watchlist(
    current_user: UserResponse = Depends(get_current_active_user),
):
    """获取用户自选股列表"""
    storage = get_storage()
    rows = storage.get_watchlist(current_user.id)
    return [dict(row) for row in rows]


@router.post("", response_model=WatchlistResponse)
async def add_to_watchlist(
    item: WatchlistCreate,
    current_user: UserResponse = Depends(get_current_active_user),
):
    """添加股票到自选列表"""
    storage = get_storage()

    # 检查是否已存在
    if storage.is_in_watchlist(current_user.id, item.stock_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该股票已在自选列表中"
        )

    # 检查数量限制
    existing = storage.get_watchlist(current_user.id)
    if len(existing) >= current_user.max_watchlist_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"自选股数量已达上限 ({current_user.max_watchlist_count})"
        )

    now = datetime.now(timezone.utc).isoformat()
    storage.add_to_watchlist(
        user_id=current_user.id,
        stock_code=item.stock_code,
    )

    return {
        "id": 0,
        "user_id": current_user.id,
        "stock_code": item.stock_code,
        "stock_name": None,
        "created_at": now
    }


@router.delete("/{stock_code}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    stock_code: str,
    current_user: UserResponse = Depends(get_current_active_user),
):
    """从自选列表中移除股票"""
    storage = get_storage()
    storage.remove_from_watchlist(current_user.id, stock_code)
    return None


@router.get("/{stock_code}/status", response_model=WatchlistStatus)
async def check_watchlist_status(
    stock_code: str,
    current_user: UserResponse = Depends(get_current_active_user),
):
    """检查股票是否在自选列表中"""
    storage = get_storage()
    exists = storage.is_in_watchlist(current_user.id, stock_code)
    return {"is_favorite": exists}
