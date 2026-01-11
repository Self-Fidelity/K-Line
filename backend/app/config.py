"""后端配置管理"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings:
    """应用配置类"""
    
    # 项目根目录（相对于backend目录的父目录）
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    
    # 数据库配置
    DATABASE_PATH: Path = BASE_DIR / "data" / "database" / "kline.db"
    
    # JWT配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24小时
    
    # CORS配置
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",  # Vite默认端口
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # Bokeh Server配置
    BOKEH_SERVER_HOST: str = os.getenv("BOKEH_SERVER_HOST", "localhost")
    BOKEH_SERVER_PORT: int = int(os.getenv("BOKEH_SERVER_PORT", "5006"))
    
    # SMTP邮件服务器配置
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.example.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    # 默认自选股数量限制
    DEFAULT_WATCHLIST_LIMIT: int = int(os.getenv("DEFAULT_WATCHLIST_LIMIT", "20"))
    
    # 日K线数据获取时间（非自选股票，交易日结束后）
    DAILY_DATA_FETCH_HOUR: int = int(os.getenv("DAILY_DATA_FETCH_HOUR", "15"))
    DAILY_DATA_FETCH_MINUTE: int = int(os.getenv("DAILY_DATA_FETCH_MINUTE", "30"))
    
    # 分时K线数据获取周期（分钟）
    MINUTE_DATA_FETCH_PERIODS: list[int] = [1, 5, 15, 30, 60]
    
    # 监控检查频率（分钟）
    MONITOR_CHECK_INTERVAL: int = int(os.getenv("MONITOR_CHECK_INTERVAL", "1"))
    
    # 交易时间
    TRADING_HOURS_START: int = 9  # 9:30
    TRADING_HOURS_END: int = 15  # 15:00


# 全局配置实例
settings = Settings()
