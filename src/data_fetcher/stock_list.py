"""股票列表管理模块"""

from typing import List, Dict, Optional
from pathlib import Path
import sys
import pandas as pd

# 添加src目录到路径
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from src.utils.logger import get_logger
from src.config import settings
from src.data_fetcher.fetcher import _create_provider

logger = get_logger(__name__)


class StockListManager:
    """股票列表管理器"""
    
    # 市场代码映射（简化为三类）
    MARKET_MAPPING = {
        "main": "主板",  # 除科创板、创业板外的主板股票
        "cyb": "创业板",  # 创业板
        "kcb": "科创板",  # 科创板
        "all": "全部",  # 全部
    }
    
    def __init__(self):
        """初始化股票列表管理器"""
        self._stock_list_cache: Optional[pd.DataFrame] = None
        self._storage = None
        self._provider = None
        self._init_stock_list_table()
    
    def _get_storage(self):
        """获取存储实例（延迟加载）"""
        if self._storage is None:
            from src.data_storage import get_storage_instance
            self._storage = get_storage_instance()
        return self._storage
    
    def _get_provider(self):
        """获取数据 Provider（延迟加载，支持配置热切换）"""
        from src.data_fetcher.fetcher import _get_data_source
        expected_source = _get_data_source()
        if self._provider is None or self._provider.name != expected_source:
            if self._provider is not None:
                logger.info(
                    f"数据源配置已变更: {self._provider.name} → {expected_source}，重新初始化 Provider"
                )
            self._provider = _create_provider()
            logger.info(f"股票列表管理器使用数据源: {self._provider.name}")
        return self._provider
    
    def get_stock_list(
        self,
        market: str = "main",
        refresh: bool = False,
        force_from_api: bool = False,
    ) -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            market: 市场类型，可选值：'main'（主板）、'cyb'（创业板）、'kcb'（科创板）、'all'（全部）
            refresh: 是否刷新缓存（已废弃，使用 force_from_api）
            force_from_api: 是否强制从 API 获取（仅管理员可用）
        
        Returns:
            股票列表 DataFrame，包含字段：
            - code: 股票代码
            - name: 股票名称
            - market: 所属市场
        """
        # 优先从数据库读取
        if not force_from_api and (self._stock_list_cache is None or refresh):
            logger.debug("尝试从数据库加载股票列表")
            df_db = self._load_from_database()
            if df_db is not None and not df_db.empty:
                self._stock_list_cache = df_db
                logger.info(f"从数据库加载了 {len(self._stock_list_cache)} 只股票")
        
        # 如果缓存为空或强制从 API 获取，则从 API 获取
        if self._stock_list_cache is None or self._stock_list_cache.empty or force_from_api:
            provider_name = self._get_provider().name
            if force_from_api:
                logger.info(f"管理员操作：从 {provider_name} API 获取股票列表")
            else:
                logger.info(f"数据库中没有股票列表，从 {provider_name} API 获取")
            try:
                self._stock_list_cache = self._get_provider().get_stock_list("all")
                # 保存到数据库
                if not self._stock_list_cache.empty:
                    self._save_to_database(self._stock_list_cache)
                    logger.info(f"从 API 获取到 {len(self._stock_list_cache)} 只股票，已保存到数据库")
            except Exception as e:
                logger.error(f"从 API 获取股票列表失败: {e}")
                # 如果 API 失败，尝试从数据库读取（即使可能为空）
                if self._stock_list_cache is None or self._stock_list_cache.empty:
                    df_db = self._load_from_database()
                    if df_db is not None and not df_db.empty:
                        self._stock_list_cache = df_db
                        logger.warning("API 获取失败，使用数据库中的旧数据")
                    else:
                        # 如果数据库也为空，返回空 DataFrame
                        logger.error("数据库和 API 都无法获取股票列表")
                        return pd.DataFrame(columns=["code", "name", "market"])
        
        # 根据市场类型过滤
        df = self._stock_list_cache.copy()
        if market != "all":
            df = df[df["market"] == market].copy()
        
        logger.debug(f"过滤后，市场类型 {market} 共有 {len(df)} 只股票")
        return df
    
    def get_stock_codes(
        self,
        market: str = "main",
        refresh: bool = False,
        force_from_api: bool = False,
    ) -> List[str]:
        """
        获取股票代码列表
        
        Args:
            market: 市场类型
            refresh: 是否刷新缓存（已废弃）
            force_from_api: 是否强制从 API 获取（仅管理员可用）
        
        Returns:
            股票代码列表
        """
        df = self.get_stock_list(market, refresh, force_from_api)
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
    
    def _init_stock_list_table(self) -> None:
        """初始化股票列表数据库表"""
        try:
            self._get_storage().init_stock_list_table()
        except Exception as e:
            logger.error(f"初始化股票列表表失败: {e}", exc_info=True)
    
    def _load_from_database(self) -> Optional[pd.DataFrame]:
        """从数据库加载股票列表"""
        try:
            return self._get_storage().load_stock_list()
        except Exception as e:
            logger.debug(f"从数据库加载股票列表失败: {e}")
            return None
    
    def _save_to_database(self, df: pd.DataFrame) -> None:
        """保存股票列表到数据库"""
        try:
            self._get_storage().save_stock_list(df)
        except Exception as e:
            logger.error(f"保存股票列表到数据库失败: {e}", exc_info=True)
    
    def clear_cache(self) -> None:
        """清除股票列表缓存"""
        self._stock_list_cache = None
        logger.debug("股票列表缓存已清除")
