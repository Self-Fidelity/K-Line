"""数据更新服务：管理定时任务和手动更新"""

import asyncio
import time
import random
import gc
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.app.config import settings
from backend.app.services.data_service import DataService
from backend.app.dependencies import get_storage
from src.utils.logger import get_logger

logger = get_logger(__name__)


# 速度档位映射
SPEED_PRESETS = {
    "slow": {"base": 5.0, "jitter_min": 2.0, "jitter_max": 5.0, "label": "慢速（N100推荐）"},
    "normal": {"base": 2.0, "jitter_min": 1.0, "jitter_max": 2.0, "label": "标准"},
    "fast": {"base": 0.5, "jitter_min": 0.2, "jitter_max": 0.5, "label": "快速"},
}


class DataUpdateService:
    """数据更新服务"""

    def __init__(self):
        """初始化服务"""
        self.data_service = DataService()
        self.storage = get_storage()
        self.scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
        self.storage.init_update_config_table()
        self._load_and_schedule_jobs()

    def _get_config(self, key: str, default: str) -> str:
        """获取配置值"""
        return self.storage.get_update_config(key, default)

    def _set_config(self, key: str, value: str):
        """设置配置值"""
        self.storage.set_update_config(key, value)

    def get_config(self) -> Dict:
        """获取当前配置"""
        return {
            "auto_update_enabled": self._get_config("auto_update_enabled", "false").lower() == "true",
            "daily_update_hour": int(self._get_config("daily_update_hour", str(settings.DAILY_DATA_FETCH_HOUR))),
            "daily_update_minute": int(self._get_config("daily_update_minute", str(settings.DAILY_DATA_FETCH_MINUTE))),
            "stock_list_update_enabled": self._get_config("stock_list_update_enabled", "false").lower() == "true",
            "stock_list_update_frequency": self._get_config("stock_list_update_frequency", "weekly"),
            "stock_list_update_hour": int(self._get_config("stock_list_update_hour", "6")),
            "stock_list_update_minute": int(self._get_config("stock_list_update_minute", "0")),
            "update_speed_preset": self._get_config("update_speed_preset", "slow"),
            "batch_size": int(self._get_config("batch_size", "50")),
            "batch_rest_seconds": int(self._get_config("batch_rest_seconds", "60")),
            "pre_update_random_wait": int(self._get_config("pre_update_random_wait", "20")),
            "incremental_update": self._get_config("incremental_update", "true").lower() == "true",
            "data_source": self._get_config("data_source", "akshare"),
        }

    def update_config(self, config: Dict):
        """更新配置"""
        for key, value in config.items():
            if value is not None:
                self._set_config(key, str(value))

        # 重新加载和调度任务
        self._reschedule_jobs()

    def get_data_source_config(self) -> Dict:
        """获取数据源配置"""
        return {
            "data_source": self._get_config("data_source", "akshare"),
            "tushare_token": self._get_config("tushare_token", ""),
        }

    def update_data_source_config(self, config: Dict):
        """更新数据源配置"""
        if config.get("data_source") is not None:
            self._set_config("data_source", config["data_source"])
        if config.get("tushare_token") is not None:
            # Token 允许为空字符串（清空）
            self._set_config("tushare_token", config["tushare_token"])

    def test_data_source(self, data_source: str) -> Dict:
        """测试数据源连接
        
        Args:
            data_source: 数据源名称 'akshare' 或 'tushare'
        
        Returns:
            {"success": bool, "message": str}
        """
        try:
            from src.data_fetcher.providers import AkShareProvider, TushareProvider
            
            if data_source == "tushare":
                token = self._get_config("tushare_token", "")
                if not token:
                    return {"success": False, "message": "Tushare token 未配置"}
                provider = TushareProvider(token=token)
            else:
                provider = AkShareProvider()
            
            return provider.test_connection()
        except Exception as e:
            logger.error(f"测试数据源 {data_source} 连接失败: {e}", exc_info=True)
            return {"success": False, "message": f"测试失败: {str(e)}"}

    def clear_data_by_source(self, data_source: str) -> int:
        """清空指定数据来源的所有日K线数据
        
        Args:
            data_source: 数据源名称 'akshare' 或 'tushare'
        
        Returns:
            删除的行数
        """
        try:
            return self.storage.clear_data_by_source(data_source)
        except Exception as e:
            logger.error(f"清空数据源 {data_source} 数据失败: {e}", exc_info=True)
            raise

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
            freq = config.get("stock_list_update_frequency", "weekly")
            if freq == "daily":
                trigger = CronTrigger(
                    day_of_week='mon-fri',
                    hour=config["stock_list_update_hour"],
                    minute=config["stock_list_update_minute"],
                    timezone='Asia/Shanghai'
                )
                freq_label = "每天"
            else:
                trigger = CronTrigger(
                    day_of_week='mon',
                    hour=config["stock_list_update_hour"],
                    minute=config["stock_list_update_minute"],
                    timezone='Asia/Shanghai'
                )
                freq_label = "每周一"

            self.scheduler.add_job(
                self._update_stock_list_job,
                trigger,
                id='stock_list_update',
                replace_existing=True
            )
            logger.info(f"已调度股票列表更新任务: {freq_label} {config['stock_list_update_hour']}:{config['stock_list_update_minute']}")

        # 启动调度器（在 asyncio 事件循环中运行时才启动）
        if not self.scheduler.running:
            try:
                self.scheduler.start()
                logger.info("定时任务调度器已启动")
            except RuntimeError as e:
                if "no running event loop" in str(e):
                    logger.debug("当前无运行中的事件循环，调度器延迟启动")
                else:
                    raise

    def _reschedule_jobs(self):
        """重新调度任务"""
        self._load_and_schedule_jobs()

    def _get_speed_config(self) -> Dict:
        """获取当前速度档位配置"""
        config = self.get_config()
        preset = config.get("update_speed_preset", "slow")
        return SPEED_PRESETS.get(preset, SPEED_PRESETS["slow"])

    async def _update_daily_data_job(self):
        """日K线数据更新任务（N100 7x24 慢速模式）"""
        start_time = time.time()
        speed = self._get_speed_config()
        config = self.get_config()
        batch_size = config.get("batch_size", 50)
        batch_rest = config.get("batch_rest_seconds", 60)
        incremental = config.get("incremental_update", True)

        logger.info(
            f"[DataUpdate] 开始日K线自动更新 | "
            f"档位: {speed['label']} | 批次: 每{batch_size}只休息{batch_rest}s | 增量: {incremental}"
        )

        try:
            df = self.data_service.get_stock_list(market="all", force_from_api=False)
            codes = df["code"].tolist()
            total = len(codes)

            success_count = 0
            skip_count = 0
            fail_count = 0

            yesterday = (datetime.now(timezone.utc).astimezone() - timedelta(days=1)).strftime("%Y%m%d")

            for i, code in enumerate(codes):
                try:
                    if incremental:
                        latest_date = self._get_latest_date_in_db(code)
                        if latest_date and latest_date >= yesterday:
                            skip_count += 1
                            continue

                    self.data_service.fetch_stock_data(code)
                    success_count += 1

                    if success_count % 25 == 0:
                        elapsed = time.time() - start_time
                        avg_per_stock = elapsed / (i + 1)
                        remain = total - i - 1
                        eta_min = (avg_per_stock * remain) / 60
                        logger.info(
                            f"[DataUpdate] 进度 {i+1}/{total} | "
                            f"成功 {success_count} 跳过 {skip_count} 失败 {fail_count} | "
                            f"均速 {avg_per_stock:.1f}s/只 | 预计还需 {eta_min:.0f} 分钟"
                        )

                except Exception as e:
                    logger.error(f"[DataUpdate] 更新股票 {code} 数据失败: {e}")
                    fail_count += 1
                finally:
                    if i < total - 1:
                        sleep_time = speed["base"] + random.uniform(speed["jitter_min"], speed["jitter_max"])
                        await asyncio.sleep(sleep_time)

                        if (i + 1) % batch_size == 0:
                            logger.info(f"[DataUpdate] 批次休息 {batch_rest}s，执行内存回收...")
                            gc.collect()
                            await asyncio.sleep(batch_rest)

            total_elapsed = (time.time() - start_time) / 3600
            logger.info(
                f"[DataUpdate] 日K线自动更新完成: "
                f"成功 {success_count} 只, 跳过 {skip_count} 只, 失败 {fail_count} 只 | "
                f"总耗时 {total_elapsed:.1f} 小时"
            )
        except Exception as e:
            logger.error(f"[DataUpdate] 日K线自动更新任务失败: {e}", exc_info=True)

    def _get_latest_date_in_db(self, stock_code: str) -> Optional[str]:
        """获取数据库中某只股票最新数据日期"""
        try:
            data_source = self.data_service._get_current_data_source()
            latest = self.data_service.storage.get_latest_date(stock_code, data_source=data_source)
            return latest
        except Exception:
            return None

    async def _update_stock_list_job(self):
        """股票列表更新任务（N100 低负载模式）"""
        config = self.get_config()
        wait = random.uniform(1, config.get("pre_update_random_wait", 20))

        logger.info(f"[DataUpdate] 开始股票列表自动更新，随机等待 {wait:.0f} 秒...")
        try:
            await asyncio.sleep(wait)
            self.data_service.get_stock_list(market="all", force_from_api=True)
            logger.info("[DataUpdate] 股票列表自动更新完成")
        except Exception as e:
            logger.error(f"[DataUpdate] 股票列表自动更新任务失败: {e}", exc_info=True)

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
