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

    def calculate_chip_distribution(self, stock_code: str, days: int = 120, price_precision: float = 0.1):
        """
        计算筹码分布 (CYQ)
        
        Args:
            stock_code: 股票代码
            days: 回溯天数 (默认最近120天)
            price_precision: 价格区间精度 (默认0.1元)
            
        Returns:
            dict: { "date": "...", "bins": [...], "chips": [...] }
        """
        import numpy as np
        
        # 1. 获取最近 N 天的数据
        # 这里需要获取比 days 更多的数据吗？通常建议从更早开始算，但为了性能暂时取最近N天
        # 获取足够长的历史数据，比如1年，以保证初始分布的影响较小
        # 但 data_service 的 get_kline_data 默认取所有或指定日期。
        # 此处我们简单实现：先获取最近 250 天数据 (约1年)
        try:
            # 引入 datetime
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days*2) # 多取一些确保覆盖
            
            start_str = start_date.strftime('%Y%m%d')
            end_str = end_date.strftime('%Y%m%d')
            
            df = self.get_kline_data(stock_code, start_date=start_str, end_date=end_str)
            if df.empty:
                return None
                
            # 截取最后 days 天，但计算最好从头算
            # 如果数据量太大，可以做截断。这里假设 df 长度适中。
            
            # 数据预处理
            # 修复字段名：数据库中通常是 turnover
            turn_col = 'turnover' if 'turnover' in df.columns else 'turn'
            
            if turn_col not in df.columns:
                logger.warning(f"{stock_code} 缺少换手率数据({turn_col})，无法计算筹码分布")
                return None
                
            # Tushare/Akshare 的 turnover 通常是百分比 (e.g. 1.5 代表 1.5%)
            # 我们需要将其转换为小数 (0.015)
            # 使用均值判断：如果均值 > 0.5，大概率是百分比（因为日换手率很少长期平均 > 50%）
            # 或者如果最大值 > 1，也大概率是百分比
            if df[turn_col].mean() > 0.5 or df[turn_col].max() > 5.0: 
                df[turn_col] = df[turn_col] / 100.0
                
            min_price = df['low'].min() * 0.9
            max_price = df['high'].max() * 1.1
            
            # Bins
            # 为了让输出更好看，bins 应该对齐到 0.00, 0.10, 0.20
            min_price = np.floor(min_price / price_precision) * price_precision
            max_price = np.ceil(max_price / price_precision) * price_precision
            
            bins = np.arange(min_price, max_price + price_precision, price_precision)
            chips = np.zeros(len(bins))
            
            # 迭代计算
            for _, row in df.iterrows():
                turnover = row[turn_col]
                # 限制最大衰减，防止异常数据
                turnover = max(0.0, min(1.0, turnover))
                
                high = row['high']
                low = row['low']
                
                # 衰减
                chips = chips * (1 - turnover)
                
                # 增加
                start_idx = int((low - min_price) / price_precision)
                end_idx = int((high - min_price) / price_precision)
                
                # 边界保护
                start_idx = max(0, min(len(bins)-1, start_idx))
                end_idx = max(0, min(len(bins)-1, end_idx))
                
                if end_idx >= start_idx:
                    # 均匀分布
                    count = end_idx - start_idx + 1
                    per_chip = turnover / count
                    chips[start_idx : end_idx + 1] += per_chip
                    
            # 归一化？通常不需要，total mass 代表当前流通中的筹码比例（理论上会接近 1.0）
            # 但为了前端展示方便，可以归一化到 max = 1 或者 sum = 1
            # 这里保持 原始值，前端如果画直方图，可能需要 max 值来定宽
            
            return {
                "bins": np.round(bins, 2).tolist(),
                "chips": chips.tolist(),
                "current_price": df.iloc[-1]['close']
            }
            
        except Exception as e:
            logger.error(f"计算筹码分布失败: {e}", exc_info=True)
            return None
