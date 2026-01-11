"""认证相关API"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlite3 import Connection

from backend.app.dependencies import get_db
from backend.app.models.auth import (
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from backend.app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from backend.app.config import settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Connection, Depends(get_db)],
) -> int:
    """获取当前用户ID"""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


def get_user_by_username(db: Connection, username: str) -> dict | None:
    """根据用户名获取用户"""
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, email, hashed_password, role, max_watchlist_count, is_active, created_at "
        "FROM users WHERE username = ?",
        (username,),
    )
    row = cursor.fetchone()
    if row:
        # 如果row_factory是Row，可以直接用dict()转换
        # 如果是tuple，需要手动构建字典
        if hasattr(row, 'keys'):
            return dict(row)
        else:
            # 手动构建字典
            return {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'hashed_password': row[3],
                'role': row[4],
                'max_watchlist_count': row[5],
                'is_active': row[6],
                'created_at': row[7],
            }
    return None


def get_user_by_id(db: Connection, user_id: int) -> dict | None:
    """根据ID获取用户"""
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, email, role, max_watchlist_count, is_active, created_at "
        "FROM users WHERE id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


def authenticate_user(db: Connection, username: str, password: str) -> dict | None:
    """验证用户"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    if not user["is_active"]:
        return None
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Connection, Depends(get_db)],
):
    """用户登录"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["id"]), "username": user["username"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout():
    """用户登出（客户端删除token即可）"""
    return {"message": "登出成功"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[Connection, Depends(get_db)],
):
    """获取当前用户信息"""
    user = get_user_by_id(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return UserResponse(**user)


def get_current_admin_user(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[Connection, Depends(get_db)],
) -> dict:
    """获取当前管理员用户（必须是admin角色）"""
    user = get_user_by_id(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限",
        )
    return user


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
    db: Annotated[Connection, Depends(get_db)],
):
    """管理员添加用户（只有管理员可以调用）"""
    # 检查用户名是否已存在
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    
    # 检查邮箱是否已存在
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在",
        )
    
    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    max_watchlist_count = user_data.max_watchlist_count or settings.DEFAULT_WATCHLIST_LIMIT
    
    cursor.execute(
        "INSERT INTO users (username, email, hashed_password, role, max_watchlist_count, is_active, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            user_data.username,
            user_data.email,
            hashed_password,
            user_data.role,
            max_watchlist_count,
            True,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    db.commit()
    user_id = cursor.lastrowid
    
    user = get_user_by_id(db, user_id)
    return UserResponse(**user)
