"""数据获取模块"""

import time
from typing import List, Dict, Optional
import pandas as pd

from src.utils.logger import get_logger
from src.config import settings
from src.data_fetcher.providers import AkShareProvider, TushareProvider

logger = get_logger(__name__)


def _get_data_source() -> str:
    """获取当前配置的数据源"""
    try:
        from src.data_storage import get_storage_instance
        storage = get_storage_instance()
        return storage.get_update_config("data_source", "akshare")
    except Exception:
        return "akshare"


def _get_tushare_token() -> str:
    """获取 Tushare token"""
    try:
        from src.data_storage import get_storage_instance
        storage = get_storage_instance()
        return storage.get_update_config("tushare_token", "")
    except Exception:
        return ""


def _create_provider(source: Optional[str] = None):
    """创建数据 Provider 实例
    
    Args:
        source: 数据源名称，如果为 None 则读取配置
    
    Returns:
        Provider 实例
    """
    src = source or _get_data_source()
    
    if src == "tushare":
        token = _get_tushare_token()
        if not token:
            logger.warning("Tushare token 未配置，回退到 AkShare")
            return AkShareProvider()
        return TushareProvider(token=token)
    
    return AkShareProvider()


class StockDataFetcher:
    """股票数据获取器
    
    支持多数据源（AkShare、Tushare），根据配置自动切换。
    """
    
    def __init__(self, data_source: Optional[str] = None):
        """初始化数据获取器
        
        Args:
            data_source: 指定数据源，如果为 None 则读取数据库配置
        """
        self._data_source = data_source
        self._provider = None
    
    def _get_provider(self):
        """获取 Provider 实例（延迟加载，支持配置热切换）"""
        expected_source = self._data_source or _get_data_source()
        if self._provider is None or self._provider.name != expected_source:
            if self._provider is not None:
                logger.info(
                    f"数据源配置已变更: {self._provider.name} → {expected_source}，重新初始化 Provider"
                )
            self._provider = _create_provider(self._data_source)
            logger.info(f"数据获取器使用数据源: {self._provider.name}")
        return self._provider
    
    def get_daily_data(
        self,
        stock_code: str,
        start_date: str = "",
        end_date: str = "",
        adjust: str = "hfq",
    ) -> pd.DataFrame:
        """
        获取单只股票的日K线数据
        
        Args:
            stock_code: 股票代码（如 '000001'）
            start_date: 开始日期（格式：'20240101'）
            end_date: 结束日期（格式：'20240101'）
            adjust: 复权类型，'hfq'（后复权）、'qfq'（前复权）、''（不复权）
        
        Returns:
            日K线数据 DataFrame
        """
        return self._get_provider().get_daily_data(stock_code, start_date, end_date, adjust)
    
    def get_latest_data(self, stock_code: str, adjust: str = "hfq") -> pd.DataFrame:
        """
        获取单只股票的最新数据（最近一个交易日）
        
        Args:
            stock_code: 股票代码
            adjust: 复权类型
        
        Returns:
            最新数据 DataFrame
        """
        return self._get_provider().get_latest_data(stock_code, adjust)
    
    def batch_fetch(
        self,
        stock_codes: List[str],
        start_date: str = "",
        end_date: str = "",
        adjust: str = "hfq",
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票的日K线数据
        
        如果 Provider 支持批量接口（如 Tushare），优先使用批量接口以大幅减少请求次数。
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
        
        Returns:
            字典，key 为股票代码，value 为对应的 DataFrame
        """
        logger.info(f"批量获取 {len(stock_codes)} 只股票的数据")
        
        provider = self._get_provider()
        
        # 如果 Provider 实现了批量接口，优先使用
        if hasattr(provider, "get_daily_data_batch"):
            try:
                return provider.get_daily_data_batch(stock_codes, start_date, end_date, adjust)
            except Exception as e:
                logger.warning(f"Provider 批量获取失败，fallback 到逐只获取: {e}")
        
        # Fallback：逐只串行获取
        results = {}
        failed_codes = []
        
        for i, code in enumerate(stock_codes, 1):
            try:
                df = provider.get_daily_data(code, start_date, end_date, adjust)
                if not df.empty:
                    results[code] = df
                else:
                    failed_codes.append(code)
                
                if i % 100 == 0:
                    logger.info(f"已处理 {i}/{len(stock_codes)} 只股票")
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"获取股票 {code} 数据失败: {e}")
                failed_codes.append(code)
                continue
        
        if failed_codes:
            logger.warning(f"共有 {len(failed_codes)} 只股票获取失败")
        
        logger.info(f"批量获取完成，成功 {len(results)} 只，失败 {len(failed_codes)} 只")
        return results
