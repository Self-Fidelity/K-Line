"""用户管理API（仅管理员）"""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlite3 import Connection
from pydantic import BaseModel, EmailStr

from backend.app.dependencies import get_db
from backend.app.api.auth import get_current_admin_user, get_password_hash
from backend.app.models.auth import UserResponse, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
    db: Annotated[Connection, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
):
    """获取用户列表"""
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, email, role, max_watchlist_count, is_active, created_at "
        "FROM users LIMIT ? OFFSET ?",
        (limit, skip),
    )
    users = []
    for row in cursor.fetchall():
        users.append(
            UserResponse(
                id=row[0],
                username=row[1],
                email=row[2],
                role=row[3],
                max_watchlist_count=row[4],
                is_active=bool(row[5]),
                created_at=row[6],
            )
        )
    return users


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
    db: Annotated[Connection, Depends(get_db)],
):
    """更新用户信息（角色、状态等）"""
    # 检查用户是否存在
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 防止修改自己的角色导致失去管理员权限（可选安全措施）
    if user_id == current_admin["id"] and user_update.role and user_update.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能移除自己的管理员权限",
        )

    # 构建更新语句
    update_fields = []
    params = []
    
    if user_update.email is not None:
        update_fields.append("email = ?")
        params.append(user_update.email)
    
    if user_update.role is not None:
        update_fields.append("role = ?")
        params.append(user_update.role)
        
    if user_update.max_watchlist_count is not None:
        update_fields.append("max_watchlist_count = ?")
        params.append(user_update.max_watchlist_count)
        
    if user_update.is_active is not None:
        update_fields.append("is_active = ?")
        params.append(user_update.is_active)
        
    if user_update.password is not None:
        update_fields.append("hashed_password = ?")
        params.append(get_password_hash(user_update.password))

    if not update_fields:
        # 没有要更新的字段，直接返回用户信息
        pass
    else:
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, tuple(params))
        db.commit()

    # 返回更新后的用户
    cursor.execute(
        "SELECT id, username, email, role, max_watchlist_count, is_active, created_at "
        "FROM users WHERE id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    return UserResponse(
        id=row[0],
        username=row[1],
        email=row[2],
        role=row[3],
        max_watchlist_count=row[4],
        is_active=bool(row[5]),
        created_at=row[6],
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
    db: Annotated[Connection, Depends(get_db)],
):
    """删除用户"""
    if user_id == current_admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己",
        )

    cursor = db.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    db.commit()
    return {"message": "用户已删除"}
