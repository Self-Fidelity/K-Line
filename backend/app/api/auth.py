"""认证相关API"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from backend.app.dependencies import get_storage
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
from backend.app.services.audit_log_service import AuditLogService
from backend.app.models.audit_log import AuditLogCreate

router = APIRouter()
log_service = AuditLogService()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _get_user_by_username(storage, username: str) -> dict | None:
    """根据用户名获取用户（内部辅助）"""
    return storage.get_user_by_username(username)


def _get_user_by_id(storage, user_id: int) -> dict | None:
    """根据ID获取用户（内部辅助）"""
    return storage.get_user_by_id(user_id)


def _authenticate_user(storage, username: str, password: str) -> dict | None:
    """验证用户（内部辅助）"""
    user = _get_user_by_username(storage, username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    if not user.get("is_active", True):
        return None
    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """用户登录"""
    storage = get_storage()
    user = _authenticate_user(storage, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 记录登录日志
    try:
        log_service.log_event(AuditLogCreate(
            user_id=user["id"],
            username=user["username"],
            action="用户登录",
            details="登录成功",
            ip_address=request.client.host if request.client else None
        ))
    except Exception as e:
        print(f"Failed to log login event: {e}")

    access_token_expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["id"]), "username": user["username"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
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


def get_current_user(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> dict:
    """获取当前用户（包含角色信息），并校验用户是否处于活跃状态"""
    storage = get_storage()
    user = _get_user_by_id(storage, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已禁用",
        )
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_active_user(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """获取当前活跃用户信息"""
    storage = get_storage()
    user = _get_user_by_id(storage, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已禁用",
        )
    # 将字典转换为 UserResponse 模型
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user.get("email"),
        role=user["role"],
        max_watchlist_count=user.get("max_watchlist_count", 20),
        is_active=bool(user.get("is_active", True)),
        created_at=user.get("created_at"),
    )


def get_current_admin_user(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> dict:
    """获取当前管理员用户（必须是admin角色）"""
    storage = get_storage()
    user = _get_user_by_id(storage, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限",
        )
    return user


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    current_admin: Annotated[dict, Depends(get_current_admin_user)],
):
    """管理员添加用户（只有管理员可以调用）"""
    storage = get_storage()
    # 检查用户名是否已存在
    if _get_user_by_username(storage, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    
    # 检查邮箱是否已存在
    if storage.check_email_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在",
        )
    
    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    max_watchlist_count = user_data.max_watchlist_count or settings.DEFAULT_WATCHLIST_LIMIT
    
    user_id = storage.create_user(
        username=user_data.username,
        password_hash=hashed_password,
        email=user_data.email,
        role=user_data.role,
        max_watchlist_count=max_watchlist_count,
        is_active=True,
    )
    
    user = _get_user_by_id(storage, user_id)
    return UserResponse(**user)


@router.post("/logout")
async def logout():
    """用户登出（客户端删除token即可）"""
    return {"message": "登出成功"}
