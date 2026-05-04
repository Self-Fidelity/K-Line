"""数据源 Provider 抽象基类"""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class BaseDataProvider(ABC):
    """数据获取 Provider 抽象基类
    
    所有数据源（AkShare、Tushare 等）必须继承此类并实现相应方法。
    """
    
    name: str = "base"
    
    @abstractmethod
    def get_daily_data(
        self,
        stock_code: str,
        start_date: str = "",
        end_date: str = "",
        adjust: str = "hfq",
    ) -> pd.DataFrame:
        """获取单只股票的日K线数据
        
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
            - pct_chg: 涨跌幅（可选）
            - change: 涨跌额（可选）
            - turnover: 换手率（可选）
        """
        pass
    
    @abstractmethod
    def get_stock_list(self, market: str = "all") -> pd.DataFrame:
        """获取股票列表
        
        Args:
            market: 市场类型，'main'（主板）、'cyb'（创业板）、'kcb'（科创板）、'all'（全部）
        
        Returns:
            股票列表 DataFrame，包含字段：
            - code: 股票代码
            - name: 股票名称
            - market: 所属市场
        """
        pass
    
    def get_latest_data(self, stock_code: str, adjust: str = "hfq") -> pd.DataFrame:
        """获取单只股票的最新数据（最近一个交易日）
        
        Args:
            stock_code: 股票代码
            adjust: 复权类型
        
        Returns:
            最新数据 DataFrame
        """
        return self.get_daily_data(stock_code, adjust=adjust).tail(1)
    
    def get_daily_data_batch(
        self,
        stock_codes: list[str],
        start_date: str = "",
        end_date: str = "",
        adjust: str = "hfq",
    ) -> dict[str, pd.DataFrame]:
        """批量获取多只股票的日K线数据
        
        默认实现为逐只串行获取。子类可覆盖此方法来利用数据源的批量查询能力。
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期（格式：'20240101'）
            end_date: 结束日期（格式：'20240101'）
            adjust: 复权类型
        
        Returns:
            字典，key 为股票代码，value 为对应的 DataFrame
        """
        results: dict[str, pd.DataFrame] = {}
        for code in stock_codes:
            df = self.get_daily_data(code, start_date, end_date, adjust)
            if not df.empty:
                results[code] = df
        return results
    
    @abstractmethod
    def test_connection(self) -> dict:
        """测试数据源连接是否可用
        
        Returns:
            {"success": bool, "message": str}
        """
        pass
