"""依赖注入模块

提供数据库会话管理，支持 SQLite（开发）和 PostgreSQL（生产）。
使用工厂函数模式，根据配置自动选择存储后端。
"""

from typing import Generator, Union
from contextlib import contextmanager

from backend.app.config import settings


def get_storage():
    """
    获取数据存储实例（工厂函数）

    根据 DATABASE_TYPE 配置自动选择存储后端：
    - postgresql: 使用 PostgreSQL + SQLAlchemy 连接池
    - sqlite: 使用 SQLite（回退方案）

    Returns:
        DataStorage 实例
    """
    if settings.DATABASE_TYPE == "postgresql":
        from src.data_storage.postgres_storage import PostgresStorage
        return PostgresStorage(
            database_url=settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
        )
    else:
        # SQLite 回退（单机/开发环境）
        from src.data_storage.sqlite_storage import SQLiteStorage
        return SQLiteStorage(database_path=str(settings.DATABASE_PATH))


def get_db() -> Generator:
    """
    获取数据库连接（向后兼容，仅用于 sqlite 场景）

    对于 PostgreSQL，使用 get_storage() 代替。
    """
    if settings.DATABASE_TYPE == "postgresql":
        raise RuntimeError(
            "get_db() 不适用于 PostgreSQL 模式，请使用 get_storage()"
        )
    import sqlite3
    conn = sqlite3.connect(str(settings.DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
