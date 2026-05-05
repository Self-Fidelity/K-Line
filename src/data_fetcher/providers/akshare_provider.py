"""AkShare 数据源 Provider 实现"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
import pandas as pd

from src.utils.logger import get_logger
from src.config import settings
from src.utils.akshare_config import ensure_akshare_configured
from src.data_fetcher.providers.base import BaseDataProvider

# 确保 akshare 已配置
ensure_akshare_configured()
import akshare as ak

logger = get_logger(__name__)


class AkShareProvider(BaseDataProvider):
    """AkShare 数据获取 Provider
    
    批量优化说明：
    - AkShare 的 stock_zh_a_hist 不支持原生批量查询（每次只能查 1 只）
    - 通过 ThreadPoolExecutor 并发 I/O 来加速，适合 N100 等低功耗设备
    - 并发数默认 4（与 N100 4 线程匹配），请求间隔 0.8s 避免反爬
    """
    
    name = "akshare"
    
    def __init__(self):
        """初始化 AkShare Provider"""
        self.retry_count = settings.AKSHARE_RETRY_COUNT
        self.retry_delay = settings.AKSHARE_RETRY_DELAY
        self.concurrency = settings.AKSHARE_CONCURRENCY
        self.request_interval = settings.AKSHARE_REQUEST_INTERVAL
    
    def _fetch_single(self, stock_code: str, start_date: str, end_date: str, adjust: str) -> tuple[str, pd.DataFrame]:
        """线程安全的单只股票获取（带间隔）"""
        try:
            df = self.get_daily_data(stock_code, start_date, end_date, adjust)
            time.sleep(self.request_interval)
            return stock_code, df
        except Exception as e:
            logger.error(f"[AkShare] 并发获取股票 {stock_code} 失败: {e}")
            return stock_code, pd.DataFrame()
    
    def get_daily_data_batch(
        self,
        stock_codes: list[str],
        start_date: str = "",
        end_date: str = "",
        adjust: str = "hfq",
    ) -> dict[str, pd.DataFrame]:
        """批量获取多只股票的日K线数据（并发优化版）
        
        利用 ThreadPoolExecutor 并发 I/O 加速，充分利用 N100 的多核能力。
        每只股票的请求间隔在单个线程内控制，避免触发东方财富反爬。
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
            adjust: 复权类型
        
        Returns:
            字典，key 为股票代码，value 为对应的 DataFrame
        """
        if not stock_codes:
            return {}
        
        logger.info(
            f"[AkShare] 并发批量获取 {len(stock_codes)} 只股票，"
            f"并发数: {self.concurrency}，单线程间隔: {self.request_interval}s"
        )
        
        results: dict[str, pd.DataFrame] = {}
        failed_codes: list[str] = []
        
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            # 提交所有任务
            future_to_code = {
                executor.submit(self._fetch_single, code, start_date, end_date, adjust): code
                for code in stock_codes
            }
            
            # 收集结果
            for i, future in enumerate(as_completed(future_to_code), 1):
                code, df = future.result()
                if not df.empty:
                    results[code] = df
                else:
                    failed_codes.append(code)
                
                if i % 100 == 0 or i == len(stock_codes):
                    logger.info(
                        f"[AkShare] 并发进度 {i}/{len(stock_codes)} | "
                        f"成功 {len(results)} 只，失败 {len(failed_codes)} 只"
                    )
        
        if failed_codes:
            logger.warning(f"[AkShare] 批量获取完成，失败 {len(failed_codes)} 只")
        
        logger.info(
            f"[AkShare] 批量获取完成，成功 {len(results)}/{len(stock_codes)} 只"
        )
        return results
    
    def get_daily_data(
        self,
        stock_code: str,
        start_date: str = "",
        end_date: str = "",
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """获取单只股票的日K线数据"""
        logger.debug(f"[AkShare] 获取股票 {stock_code} 的日K线数据，日期范围: {start_date} ~ {end_date}")
        
        for attempt in range(self.retry_count):
            try:
                params = {
                    "symbol": stock_code,
                    "period": "daily",
                }
                
                if start_date:
                    params["start_date"] = start_date
                if end_date:
                    params["end_date"] = end_date
                
                if adjust == "hfq":
                    params["adjust"] = "hfq"
                    df = ak.stock_zh_a_hist(**params)
                elif adjust == "qfq":
                    params["adjust"] = "qfq"
                    df = ak.stock_zh_a_hist(**params)
                else:
                    params["adjust"] = ""
                    df = ak.stock_zh_a_hist(**params)
                
                if df.empty:
                    logger.warning(f"[AkShare] 股票 {stock_code} 未获取到数据")
                    return pd.DataFrame()
                
                df = self._standardize_columns(df)
                logger.debug(f"[AkShare] 成功获取股票 {stock_code} {len(df)} 条数据")
                return df
                
            except Exception as e:
                if attempt < self.retry_count - 1:
                    logger.warning(
                        f"[AkShare] 获取股票 {stock_code} 数据失败（尝试 {attempt + 1}/{self.retry_count}）: {e}"
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"[AkShare] 获取股票 {stock_code} 数据失败: {e}", exc_info=True)
                    raise
        
        return pd.DataFrame()
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化 DataFrame 列名"""
        column_mapping = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "涨跌幅": "pct_chg",
            "涨跌额": "change",
            "换手率": "turnover",
        }
        
        df = df.rename(columns=column_mapping)
        
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        
        required_columns = ["date", "open", "close", "high", "low", "volume", "amount"]
        available_columns = [col for col in required_columns if col in df.columns]
        
        optional_columns = ["pct_chg", "change", "turnover"]
        for col in optional_columns:
            if col in df.columns:
                available_columns.append(col)
        
        df = df[available_columns].copy()
        return df
    
    def get_stock_list(self, market: str = "all") -> pd.DataFrame:
        """获取股票列表"""
        try:
            df_all = ak.stock_info_a_code_name()
            
            # 标准化列名
            if "code" not in df_all.columns:
                if "股票代码" in df_all.columns:
                    df_all.rename(columns={"股票代码": "code", "股票简称": "name"}, inplace=True)
            
            # 根据股票代码判断市场类型
            def _detect_market(code: str) -> str:
                if code.startswith("688") or code.startswith("689"):
                    return "kcb"
                elif code.startswith("3"):
                    return "cyb"
                else:
                    return "main"
            
            df_all["market"] = df_all["code"].apply(_detect_market)
            
            if market != "all":
                df_all = df_all[df_all["market"] == market].copy()
            
            df = df_all[["code", "name", "market"]].copy()
            logger.debug(f"[AkShare] 获取到 {len(df)} 只股票，市场: {market}")
            return df
            
        except Exception as e:
            logger.error(f"[AkShare] 获取股票列表失败: {e}", exc_info=True)
            raise
    
    def test_connection(self) -> dict:
        """测试 AkShare 连接"""
        try:
            # 尝试获取一只常见股票的数据来测试连接
            df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20240101", end_date="20240105", adjust="")
            if not df.empty:
                return {"success": True, "message": "AkShare 连接正常"}
            return {"success": False, "message": "AkShare 返回空数据"}
        except Exception as e:
            return {"success": False, "message": f"AkShare 连接失败: {str(e)}"}
