"""配置管理模块"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()


class Settings:
    """应用配置类"""
    
    # 项目根目录
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    
    # 数据目录
    DATA_DIR: Path = BASE_DIR / "data"
    DATABASE_DIR: Path = DATA_DIR / "database"
    CSV_DIR: Path = DATA_DIR / "csv"
    IMAGES_DIR: Path = DATA_DIR / "images"  # 图表输出目录
    STRATEGY_RESULTS_DIR: Path = DATA_DIR / "strategy_results"  # 策略分析结果目录
    
    # 日志目录
    LOG_DIR: Path = BASE_DIR / "logs"
    
    # 数据库配置
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "postgresql")  # sqlite | postgresql
    DATABASE_NAME: str = "kline.db"
    DATABASE_PATH: Path = DATABASE_DIR / DATABASE_NAME

    # PostgreSQL 配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://kline_user:kline_pass@localhost:5432/kline_db",
    )
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "kline.log"
    LOG_FILE_PATH: Path = LOG_DIR / LOG_FILE
    
    # 数据源配置（akshare）
    AKSHARE_TIMEOUT: int = int(os.getenv("AKSHARE_TIMEOUT", "30"))
    AKSHARE_RETRY_COUNT: int = int(os.getenv("AKSHARE_RETRY_COUNT", "3"))
    AKSHARE_RETRY_DELAY: int = int(os.getenv("AKSHARE_RETRY_DELAY", "1"))
    
    # 数据获取配置
    DEFAULT_MARKET: str = "main"  # 沪深主板
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))  # 批量处理大小
    
    # 策略配置
    STRATEGY_DIR: Path = BASE_DIR / "src" / "strategy"
    STRATEGY_PLUGIN_DIR: Path = STRATEGY_DIR / "plugins"
    
    # 数据导出配置
    EXPORT_DIR: Path = CSV_DIR
    EXPORT_FORMAT: str = "csv"
    
    # 图表输出配置
    CHART_DIR: Path = IMAGES_DIR
    CHART_FORMAT: str = "html"  # 使用HTML格式（Bokeh）
    
    @classmethod
    def init_directories(cls) -> None:
        """初始化必要的目录"""
        directories = [
            cls.DATA_DIR,
            cls.DATABASE_DIR,
            cls.CSV_DIR,
            cls.LOG_DIR,
            cls.STRATEGY_PLUGIN_DIR,
            cls.EXPORT_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_database_path(cls) -> str:
        """获取数据库路径（字符串形式）"""
        cls.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        return str(cls.DATABASE_PATH)
    
    @classmethod
    def get_log_file_path(cls) -> str:
        """获取日志文件路径（字符串形式）"""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        return str(cls.LOG_FILE_PATH)


# 全局配置实例
settings = Settings()
