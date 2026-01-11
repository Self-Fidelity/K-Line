"""股票列表管理模块"""

from typing import List, Dict, Optional
import akshare as ak
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class StockListManager:
    """股票列表管理器"""
    
    # 市场代码映射
    MARKET_MAPPING = {
        "main": ["上海A股", "深圳A股"],  # 沪深主板
        "sse": ["上海A股"],  # 上海主板
        "szse": ["深圳A股"],  # 深圳主板
        "all": ["上海A股", "深圳A股", "创业板", "科创板"],  # 全部
    }
    
    def __init__(self):
        """初始化股票列表管理器"""
        self._stock_list_cache: Optional[pd.DataFrame] = None
    
    def get_stock_list(
        self,
        market: str = "main",
        refresh: bool = False,
    ) -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            market: 市场类型，可选值：'main'（沪深主板）、'sse'（上海主板）、
                   'szse'（深圳主板）、'all'（全部）
            refresh: 是否刷新缓存
        
        Returns:
            股票列表 DataFrame，包含字段：
            - code: 股票代码
            - name: 股票名称
            - market: 所属市场
        """
        if self._stock_list_cache is None or refresh:
            logger.info(f"获取股票列表，市场类型: {market}")
            self._stock_list_cache = self._fetch_stock_list(market)
            logger.info(f"获取到 {len(self._stock_list_cache)} 只股票")
        
        return self._stock_list_cache.copy()
    
    def _fetch_stock_list(self, market: str) -> pd.DataFrame:
        """
        从 akshare 获取股票列表
        
        Args:
            market: 市场类型
        
        Returns:
            股票列表 DataFrame
        """
        market_types = self.MARKET_MAPPING.get(market, self.MARKET_MAPPING["main"])
        
        all_stocks = []
        
        try:
            # 获取上海A股
            if "上海A股" in market_types:
                sse_stocks = ak.stock_info_a_code_name()
                sse_stocks["market"] = "SSE"
                all_stocks.append(sse_stocks)
                logger.debug(f"获取上海A股 {len(sse_stocks)} 只")
            
            # 获取深圳A股
            if "深圳A股" in market_types:
                # akshare 的 stock_info_a_code_name 已经包含了沪深两市
                # 如果需要区分，可以进一步处理
                pass
            
            # 合并结果
            if all_stocks:
                df = pd.concat(all_stocks, ignore_index=True)
            else:
                # 如果 market_types 为空或只包含已处理的类型，使用默认方式
                df = ak.stock_info_a_code_name()
                df["market"] = "ALL"
            
            # 标准化列名
            if "code" not in df.columns:
                if "股票代码" in df.columns:
                    df.rename(columns={"股票代码": "code", "股票简称": "name"}, inplace=True)
                else:
                    # 根据实际返回的列名调整
                    df.columns = ["code", "name", "market"] if "market" in df.columns else ["code", "name"]
            
            # 过滤市场类型（如果指定了特定市场）
            if market != "all" and "market" in df.columns:
                # 这里可以根据需要进一步过滤
                pass
            
            # 确保列顺序
            if "market" not in df.columns:
                df["market"] = market.upper()
            
            df = df[["code", "name", "market"]].copy()
            
            # 过滤掉ST股票（可选）
            # df = df[~df["name"].str.contains("ST")]
            
            return df
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}", exc_info=True)
            raise
    
    def get_stock_codes(
        self,
        market: str = "main",
        refresh: bool = False,
    ) -> List[str]:
        """
        获取股票代码列表
        
        Args:
            market: 市场类型
            refresh: 是否刷新缓存
        
        Returns:
            股票代码列表
        """
        df = self.get_stock_list(market, refresh)
        return df["code"].tolist()
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """
        获取单只股票的基本信息
        
        Args:
            stock_code: 股票代码
        
        Returns:
            股票信息字典，如果未找到返回 None
        """
        df = self.get_stock_list()
        stock = df[df["code"] == stock_code]
        
        if stock.empty:
            return None
        
        return stock.iloc[0].to_dict()
    
    def clear_cache(self) -> None:
        """清除股票列表缓存"""
        self._stock_list_cache = None
        logger.debug("股票列表缓存已清除")
