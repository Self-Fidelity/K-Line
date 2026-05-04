"""数据存储模块"""

from .storage import DataStorage
from .sqlite_storage import SQLiteStorage
from .export import DataExporter

__all__ = ["DataStorage", "SQLiteStorage", "DataExporter", "get_storage_instance"]


# 简单的全局单例（延迟初始化）
_storage_instance = None


def get_storage_instance():
    """获取数据存储实例（src 层工厂函数，不依赖 backend）"""
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    from src.config import settings

    if settings.DATABASE_TYPE == "postgresql":
        from .postgres_storage import PostgresStorage
        _storage_instance = PostgresStorage(
            database_url=settings.DATABASE_URL,
        )
    else:
        _storage_instance = SQLiteStorage(
            database_path=str(settings.DATABASE_PATH)
        )
    return _storage_instance
