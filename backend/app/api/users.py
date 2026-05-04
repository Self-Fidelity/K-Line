"""用户管理API（仅管理员）"""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from backend.app.dependencies import get_storage
from backend.app.api.auth import get_current_admin_user, get_password_hash
from backend.app.models.auth import UserResponse, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
    skip: int = 0,
    limit: int = 100,
):
    """获取用户列表"""
    storage = get_storage()
    users = storage.list_users(skip=skip, limit=limit)
    return [
        UserResponse(
            id=u["id"],
            username=u["username"],
            email=u.get("email"),
            role=u["role"],
            max_watchlist_count=u.get("max_watchlist_count", 20),
            is_active=bool(u.get("is_active", True)),
            created_at=u.get("created_at"),
        )
        for u in users
    ]


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
):
    """更新用户信息（角色、状态等）"""
    storage = get_storage()
    # 检查用户是否存在
    existing = storage.get_user_by_id(user_id)
    if not existing:
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

    # 构建更新字段
    fields = {}
    if user_update.email is not None:
        fields["email"] = user_update.email
    if user_update.role is not None:
        fields["role"] = user_update.role
    if user_update.max_watchlist_count is not None:
        fields["max_watchlist_count"] = user_update.max_watchlist_count
    if user_update.is_active is not None:
        fields["is_active"] = 1 if user_update.is_active else 0
    if user_update.password is not None:
        fields["hashed_password"] = get_password_hash(user_update.password)

    if fields:
        storage.update_user(user_id, **fields)

    # 返回更新后的用户
    user = storage.get_user_by_id(user_id)
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user.get("email"),
        role=user["role"],
        max_watchlist_count=user.get("max_watchlist_count", 20),
        is_active=bool(user.get("is_active", True)),
        created_at=user.get("created_at"),
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
):
    """删除用户"""
    if user_id == current_admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己",
        )

    storage = get_storage()
    if not storage.delete_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return {"message": "用户已删除"}
