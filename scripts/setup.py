"""数据库初始化脚本"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger()


def main():
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    
    # 初始化目录
    settings.init_directories()
    logger.info("目录初始化完成")
    
    # 根据配置选择存储后端并初始化数据库表
    database_type = settings.DATABASE_TYPE.lower()
    if database_type == "postgresql":
        from src.data_storage.postgres_storage import PostgresStorage
        storage = PostgresStorage()
        logger.info("PostgreSQL 数据库初始化完成")
    else:
        from src.data_storage.sqlite_storage import SQLiteStorage
        storage = SQLiteStorage()
        logger.info("SQLite 数据库初始化完成")
    
    logger.info("初始化完成！")


if __name__ == "__main__":
    main()
