"""数据服务：封装SQLiteStorage"""

from typing import Optional
import pandas as pd
from pathlib import Path
import sys

# 添加src目录到路径
backend_dir = Path(__file__).parent.parent.parent
src_dir = backend_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from src.data_storage.sqlite_storage import SQLiteStorage
from src.data_fetcher.fetcher import StockDataFetcher
from src.data_fetcher.stock_list import StockListManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataService:
    """数据服务类"""
    
    def __init__(self):
        """初始化数据服务"""
        self.storage = SQLiteStorage()
        self.fetcher = StockDataFetcher()
        self.stock_list_manager = StockListManager()
    
    def get_stock_name(self, stock_code: str) -> Optional[str]:
        """获取股票名称"""
        try:
            df = self.stock_list_manager.get_stock_list(market='all')
            row = df[df['code'] == stock_code]
            if not row.empty:
                return row.iloc[0]['name']
            return None
        except Exception as e:
            logger.error(f"获取股票名称失败: {e}")
            return None

    def get_stock_list(
        self, 
        market: str = "main", 
        refresh: bool = False,
        force_from_api: bool = False,
    ) -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            market: 市场类型，'main'（沪深主板）、'sse'（上海主板）、
                   'szse'（深圳主板）、'cyb'（创业板）、'kcb'（科创板）、'all'（全部）
            refresh: 是否刷新缓存（已废弃，仅用于兼容）
            force_from_api: 是否强制从 API 获取（仅管理员可用）
        
        Returns:
            股票列表 DataFrame，包含字段：code, name, market, latest_date
        """
        df = self.stock_list_manager.get_stock_list(
            market=market, 
            refresh=refresh,
            force_from_api=force_from_api,
        )
        
        # 添加最新数据日期
        df["latest_date"] = df["code"].apply(lambda code: self._get_latest_date(code))
        
        return df
    
    def _get_latest_date(self, stock_code: str) -> Optional[str]:
        """获取股票最新数据日期"""
        try:
            return self.storage.get_latest_date(stock_code)
        except Exception as e:
            logger.error(f"获取最新数据日期失败: {e}")
            return None
    
    def get_kline_data(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取日K线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期（格式：'20240101' 或 '2024-01-01'）
            end_date: 结束日期（格式：'20240101' 或 '2024-01-01'）
        
        Returns:
            日K线数据 DataFrame
        """
        # 移除日期中的连字符，以匹配数据库中的存储格式 YYYYMMDD
        if start_date:
            start_date = start_date.replace("-", "")
        if end_date:
            end_date = end_date.replace("-", "")

        return self.storage.get_daily_data(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
        )
    
    def get_minute_kline_data(
        self,
        stock_code: str,
        period: str,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取分时K线数据
        
        Args:
            stock_code: 股票代码
            period: 分时周期，'1', '5', '15', '30', '60'
            start_datetime: 开始日期时间（格式：'20240101 0930'）
            end_datetime: 结束日期时间（格式：'20240101 1500'）
        
        Returns:
            分时K线数据 DataFrame
        """
        # TODO: 实现分时数据获取（需要在SQLiteStorage中添加相应方法）
        raise NotImplementedError("分时数据获取功能待实现")
    
    def fetch_stock_data(self, stock_code: str) -> str:
        """
        触发数据获取（异步任务）
        
        Args:
            stock_code: 股票代码
        
        Returns:
            任务ID（目前返回股票代码）
        """
        # TODO: 实现异步任务（使用Celery或BackgroundTasks）
        # 目前先同步获取
        data = self.fetcher.get_daily_data(stock_code)
        if not data.empty:
            self.storage.save_daily_data(data, stock_code)
        return stock_code
