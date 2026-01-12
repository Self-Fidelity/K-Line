"""数据更新服务：管理定时任务和手动更新"""

import sqlite3
from typing import Optional, Dict
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.app.config import settings
from backend.app.services.data_service import DataService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataUpdateService:
    """数据更新服务"""
    
    def __init__(self):
        """初始化服务"""
        self.data_service = DataService()
        self.scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
        self._init_config_table()
        self._load_and_schedule_jobs()
    
    def _init_config_table(self):
        """初始化配置表"""
        try:
            conn = sqlite3.connect(settings.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_update_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"初始化配置表失败: {e}", exc_info=True)
    
    def _get_config(self, key: str, default: str) -> str:
        """获取配置值"""
        try:
            conn = sqlite3.connect(settings.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM data_update_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else default
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            return default
    
    def _set_config(self, key: str, value: str):
        """设置配置值"""
        try:
            conn = sqlite3.connect(settings.DATABASE_PATH)
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                "INSERT OR REPLACE INTO data_update_config (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, now)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"设置配置失败: {e}", exc_info=True)
    
    def get_config(self) -> Dict:
        """获取当前配置"""
        return {
            "auto_update_enabled": self._get_config("auto_update_enabled", "false").lower() == "true",
            "daily_update_hour": int(self._get_config("daily_update_hour", str(settings.DAILY_DATA_FETCH_HOUR))),
            "daily_update_minute": int(self._get_config("daily_update_minute", str(settings.DAILY_DATA_FETCH_MINUTE))),
            "stock_list_update_enabled": self._get_config("stock_list_update_enabled", "false").lower() == "true",
            "stock_list_update_hour": int(self._get_config("stock_list_update_hour", "9")),
            "stock_list_update_minute": int(self._get_config("stock_list_update_minute", "0")),
        }
    
    def update_config(self, config: Dict):
        """更新配置"""
        for key, value in config.items():
            if value is not None:
                self._set_config(key, str(value))
        
        # 重新加载和调度任务
        self._reschedule_jobs()
    
    def _load_and_schedule_jobs(self):
        """加载配置并调度任务"""
        config = self.get_config()
        
        # 清除现有任务
        self.scheduler.remove_all_jobs()
        
        # 调度日K线数据更新任务
        if config["auto_update_enabled"]:
            self.scheduler.add_job(
                self._update_daily_data_job,
                CronTrigger(
                    day_of_week='mon-fri',
                    hour=config["daily_update_hour"],
                    minute=config["daily_update_minute"],
                    timezone='Asia/Shanghai'
                ),
                id='daily_data_update',
                replace_existing=True
            )
            logger.info(f"已调度日K线数据更新任务: {config['daily_update_hour']}:{config['daily_update_minute']}")
        
        # 调度股票列表更新任务
        if config["stock_list_update_enabled"]:
            self.scheduler.add_job(
                self._update_stock_list_job,
                CronTrigger(
                    day_of_week='mon-fri',
                    hour=config["stock_list_update_hour"],
                    minute=config["stock_list_update_minute"],
                    timezone='Asia/Shanghai'
                ),
                id='stock_list_update',
                replace_existing=True
            )
            logger.info(f"已调度股票列表更新任务: {config['stock_list_update_hour']}:{config['stock_list_update_minute']}")
        
        # 启动调度器
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("定时任务调度器已启动")
    
    def _reschedule_jobs(self):
        """重新调度任务"""
        self._load_and_schedule_jobs()
    
    async def _update_daily_data_job(self):
        """日K线数据更新任务"""
        logger.info("开始执行日K线数据自动更新任务")
        try:
            # 获取所有股票代码
            df = self.data_service.get_stock_list(market="all", force_from_api=False)
            codes = df["code"].tolist()
            
            success_count = 0
            for code in codes:
                try:
                    self.data_service.fetch_stock_data(code)
                    success_count += 1
                    if success_count % 100 == 0:
                        logger.info(f"已更新 {success_count}/{len(codes)} 只股票")
                except Exception as e:
                    logger.error(f"更新股票 {code} 数据失败: {e}")
            
            logger.info(f"日K线数据自动更新完成，成功 {success_count}/{len(codes)} 只")
        except Exception as e:
            logger.error(f"日K线数据自动更新任务失败: {e}", exc_info=True)
    
    async def _update_stock_list_job(self):
        """股票列表更新任务"""
        logger.info("开始执行股票列表自动更新任务")
        try:
            self.data_service.get_stock_list(market="all", force_from_api=True)
            logger.info("股票列表自动更新完成")
        except Exception as e:
            logger.error(f"股票列表自动更新任务失败: {e}", exc_info=True)
    
    def start_scheduler(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("定时任务调度器已启动")
    
    def stop_scheduler(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("定时任务调度器已停止")
    
    def get_scheduler_status(self) -> Dict:
        """获取调度器状态"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            })
        
        return {
            "running": self.scheduler.running,
            "jobs": jobs,
        }
