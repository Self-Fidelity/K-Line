from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import sqlite3
from datetime import datetime, timezone

from backend.app.dependencies import get_db
from backend.app.models.watchlist import WatchlistCreate, WatchlistResponse, WatchlistStatus
from backend.app.models.auth import UserResponse
from backend.app.api.auth import get_current_active_user

router = APIRouter()

@router.get("", response_model=List[WatchlistResponse])
async def get_watchlist(
    current_user: UserResponse = Depends(get_current_active_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """获取用户自选股列表"""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT w.id, w.user_id, w.stock_code, s.name as stock_name, w.created_at 
        FROM watchlist w 
        LEFT JOIN stock_list s ON w.stock_code = s.code 
        WHERE w.user_id = ? 
        ORDER BY w.created_at DESC
        """,
        (current_user.id,)
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@router.post("", response_model=WatchlistResponse)
async def add_to_watchlist(
    item: WatchlistCreate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """添加股票到自选列表"""
    cursor = db.cursor()
    
    # 检查是否已存在
    cursor.execute(
        "SELECT id FROM watchlist WHERE user_id = ? AND stock_code = ?",
        (current_user.id, item.stock_code)
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该股票已在自选列表中"
        )
    
    # 检查数量限制 (可选，暂不强制，遵循init_db里的max_watchlist_count逻辑)
    cursor.execute("SELECT COUNT(*) FROM watchlist WHERE user_id = ?", (current_user.id,))
    count = cursor.fetchone()[0]
    if count >= current_user.max_watchlist_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"自选股数量已达上限 ({current_user.max_watchlist_count})"
        )

    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO watchlist (user_id, stock_code, created_at) VALUES (?, ?, ?)",
        (current_user.id, item.stock_code, now)
    )
    db.commit()
    
    watchlist_id = cursor.lastrowid
    
    # 获取股票名称
    cursor.execute("SELECT name FROM stock_list WHERE code = ?", (item.stock_code,))
    stock_row = cursor.fetchone()
    stock_name = stock_row[0] if stock_row else None
    
    return {
        "id": watchlist_id,
        "user_id": current_user.id,
        "stock_code": item.stock_code,
        "stock_name": stock_name,
        "created_at": now
    }

@router.delete("/{stock_code}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    stock_code: str,
    current_user: UserResponse = Depends(get_current_active_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """从自选列表中移除股票"""
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM watchlist WHERE user_id = ? AND stock_code = ?",
        (current_user.id, stock_code)
    )
    db.commit()
    return None

@router.get("/{stock_code}/status", response_model=WatchlistStatus)
async def check_watchlist_status(
    stock_code: str,
    current_user: UserResponse = Depends(get_current_active_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """检查股票是否在自选列表中"""
    cursor = db.cursor()
    cursor.execute(
        "SELECT 1 FROM watchlist WHERE user_id = ? AND stock_code = ?",
        (current_user.id, stock_code)
    )
    exists = cursor.fetchone() is not None
    return {"is_favorite": exists}
