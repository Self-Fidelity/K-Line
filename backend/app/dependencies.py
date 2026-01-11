"""依赖注入模块"""

from typing import Generator
import sqlite3
from pathlib import Path

from backend.app.config import settings


def get_db() -> Generator:
    """获取数据库连接"""
    # 设置check_same_thread=False以支持FastAPI的多线程环境
    # 每个请求都会创建新的连接，所以这是安全的
    conn = sqlite3.connect(str(settings.DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
