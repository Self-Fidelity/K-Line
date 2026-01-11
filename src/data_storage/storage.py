"""数据存储接口定义"""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class DataStorage(ABC):
    """数据存储抽象基类"""
    
    @abstractmethod
    def save_daily_data(
        self,
        data: pd.DataFrame,
        stock_code: str,
    ) -> bool:
        """
        保存日K线数据
        
        Args:
            data: 日K线数据 DataFrame
            stock_code: 股票代码
        
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    def get_daily_data(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取日K线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期（格式：'20240101'）
            end_date: 结束日期（格式：'20240101'）
        
        Returns:
            日K线数据 DataFrame
        """
        pass
    
    @abstractmethod
    def get_latest_date(self, stock_code: str) -> Optional[str]:
        """
        获取指定股票的最新数据日期
        
        Args:
            stock_code: 股票代码
        
        Returns:
            最新日期字符串（格式：'20240101'），如果没有数据返回 None
        """
        pass
    
    @abstractmethod
    def check_data_exists(
        self,
        stock_code: str,
        trade_date: str,
    ) -> bool:
        """
        检查指定日期的数据是否存在
        
        Args:
            stock_code: 股票代码
            trade_date: 交易日期（格式：'20240101'）
        
        Returns:
            如果数据存在返回 True，否则返回 False
        """
        pass
    
    @abstractmethod
    def get_all_stocks(self) -> list[str]:
        """
        获取数据库中所有股票代码列表
        
        Returns:
            股票代码列表
        """
        pass
