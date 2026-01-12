"""数据获取模块"""

import time
from typing import List, Dict, Optional
import pandas as pd

from src.utils.logger import get_logger
from src.config import settings
# 在导入 akshare 之前先配置它
from src.utils.akshare_config import ensure_akshare_configured

# 确保 akshare 已配置
ensure_akshare_configured()

# 现在导入 akshare
import akshare as ak

logger = get_logger(__name__)


class StockDataFetcher:
    """股票数据获取器"""
    
    def __init__(self):
        """初始化数据获取器"""
        self.retry_count = settings.AKSHARE_RETRY_COUNT
        self.retry_delay = settings.AKSHARE_RETRY_DELAY
    
    def get_daily_data(
        self,
        stock_code: str,
        start_date: str = "",
        end_date: str = "",
        adjust: str = "hfq",  # 后复权
    ) -> pd.DataFrame:
        """
        获取单只股票的日K线数据
        
        Args:
            stock_code: 股票代码（如 '000001'）
            start_date: 开始日期（格式：'20240101'）
            end_date: 结束日期（格式：'20240101'）
            adjust: 复权类型，'hfq'（后复权）、'qfq'（前复权）、''（不复权）
        
        Returns:
            日K线数据 DataFrame，包含字段：
            - date: 交易日期
            - open: 开盘价
            - close: 收盘价
            - high: 最高价
            - low: 最低价
            - volume: 成交量
            - amount: 成交额
        """
        logger.debug(f"获取股票 {stock_code} 的日K线数据，日期范围: {start_date} ~ {end_date}")
        
        for attempt in range(self.retry_count):
            try:
                # 构建参数，如果日期为空则不传递
                params = {
                    "symbol": stock_code,
                    "period": "daily",
                }
                
                if start_date:
                    params["start_date"] = start_date
                if end_date:
                    params["end_date"] = end_date
                
                # 使用 akshare 获取后复权数据
                if adjust == "hfq":
                    params["adjust"] = "hfq"  # 后复权
                    df = ak.stock_zh_a_hist(**params)
                else:
                    params["adjust"] = ""  # 不复权
                    df = ak.stock_zh_a_hist(**params)
                
                if df.empty:
                    logger.warning(f"股票 {stock_code} 未获取到数据")
                    return pd.DataFrame()
                
                # 标准化列名
                df = self._standardize_columns(df)
                
                logger.debug(f"成功获取股票 {stock_code} {len(df)} 条数据")
                return df
                
            except Exception as e:
                if attempt < self.retry_count - 1:
                    logger.warning(
                        f"获取股票 {stock_code} 数据失败（尝试 {attempt + 1}/{self.retry_count}）: {e}"
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"获取股票 {stock_code} 数据失败: {e}", exc_info=True)
                    raise
        
        return pd.DataFrame()
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化 DataFrame 列名
        
        Args:
            df: 原始 DataFrame
        
        Returns:
            标准化后的 DataFrame
        """
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
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 确保日期列为 datetime 类型
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        
        # 选择需要的列
        required_columns = ["date", "open", "close", "high", "low", "volume", "amount"]
        available_columns = [col for col in required_columns if col in df.columns]
        
        # 添加可选列
        optional_columns = ["pct_chg", "change", "turnover"]
        for col in optional_columns:
            if col in df.columns:
                available_columns.append(col)
        
        df = df[available_columns].copy()
        
        return df
    
    def get_latest_data(self, stock_code: str, adjust: str = "hfq") -> pd.DataFrame:
        """
        获取单只股票的最新数据（最近一个交易日）
        
        Args:
            stock_code: 股票代码
            adjust: 复权类型
        
        Returns:
            最新数据 DataFrame
        """
        return self.get_daily_data(stock_code, adjust=adjust).tail(1)
    
    def batch_fetch(
        self,
        stock_codes: List[str],
        start_date: str = "",
        end_date: str = "",
        adjust: str = "hfq",
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票的日K线数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
        
        Returns:
            字典，key 为股票代码，value 为对应的 DataFrame
        """
        logger.info(f"批量获取 {len(stock_codes)} 只股票的数据")
        
        results = {}
        failed_codes = []
        
        for i, code in enumerate(stock_codes, 1):
            try:
                df = self.get_daily_data(code, start_date, end_date, adjust)
                if not df.empty:
                    results[code] = df
                else:
                    failed_codes.append(code)
                
                # 进度日志
                if i % 100 == 0:
                    logger.info(f"已处理 {i}/{len(stock_codes)} 只股票")
                
                # 避免请求过快
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"获取股票 {code} 数据失败: {e}")
                failed_codes.append(code)
                continue
        
        if failed_codes:
            logger.warning(f"共有 {len(failed_codes)} 只股票获取失败")
        
        logger.info(f"批量获取完成，成功 {len(results)} 只，失败 {len(failed_codes)} 只")
        return results
