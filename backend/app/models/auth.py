"""认证相关模型"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据模型"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class UserCreate(BaseModel):
    """用户创建模型"""
    username: str
    email: EmailStr
    password: str
    role: str = "user"
    max_watchlist_count: Optional[int] = None


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    role: str
    max_watchlist_count: int
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    max_watchlist_count: Optional[int] = None
    is_active: Optional[bool] = None
