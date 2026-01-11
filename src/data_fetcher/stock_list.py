"""股票列表管理模块"""

from typing import List, Dict, Optional
from pathlib import Path
import sys
import akshare as ak
import pandas as pd
import sqlite3

# 添加src目录到路径
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from src.utils.logger import get_logger
from src.config import settings

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
        self._init_stock_list_table()
    
    def get_stock_list(
        self,
        market: str = "main",
        refresh: bool = False,
    ) -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            market: 市场类型，可选值：'main'（主板）、'cyb'（创业板）、'kcb'（科创板）、'all'（全部）
            refresh: 是否刷新缓存
        
        Returns:
            股票列表 DataFrame，包含字段：
            - code: 股票代码
            - name: 股票名称
            - market: 所属市场
        """
        # 总是获取全部股票列表，然后根据market参数过滤
        if self._stock_list_cache is None or refresh:
            logger.info(f"从数据源获取股票列表")
            self._stock_list_cache = self._fetch_stock_list("all")
            logger.info(f"获取到 {len(self._stock_list_cache)} 只股票")
        
        # 根据市场类型过滤
        df = self._stock_list_cache.copy()
        if market != "all":
            df = df[df["market"] == market].copy()
        
        logger.info(f"过滤后，市场类型 {market} 共有 {len(df)} 只股票")
        return df
    
    def _fetch_stock_list(self, market: str) -> pd.DataFrame:
        """
        从 akshare 获取股票列表
        
        Args:
            market: 市场类型，'main'（主板）、'cyb'（创业板）、'kcb'（科创板）、'all'（全部）
        
        Returns:
            股票列表 DataFrame
        """
        try:
            # 获取所有A股股票列表
            df_all = ak.stock_info_a_code_name()
            
            # 标准化列名
            if "code" not in df_all.columns:
                if "股票代码" in df_all.columns:
                    df_all.rename(columns={"股票代码": "code", "股票简称": "name"}, inplace=True)
            
            # 根据股票代码判断市场类型
            def _detect_market(code: str) -> str:
                """根据股票代码判断市场"""
                if code.startswith("688") or code.startswith("689"):
                    # 688/689开头是科创板
                    return "kcb"
                elif code.startswith("3"):
                    # 3开头是创业板
                    return "cyb"
                else:
                    # 其他都是主板（包括6开头的上海主板和0开头的深圳主板）
                    return "main"
            
            # 添加市场列
            df_all["market"] = df_all["code"].apply(_detect_market)
            
            # 根据市场类型过滤
            if market != "all":
                df_all = df_all[df_all["market"] == market].copy()
            
            # 确保列顺序
            df = df_all[["code", "name", "market"]].copy()
            
            logger.debug(f"获取到 {len(df)} 只股票，市场: {market}")
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
    
    def _init_stock_list_table(self) -> None:
        """初始化股票列表数据库表"""
        try:
            database_path = settings.get_database_path()
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_list (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    market TEXT NOT NULL,
                    update_time TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"初始化股票列表表失败: {e}", exc_info=True)
    
    def _load_from_database(self) -> Optional[pd.DataFrame]:
        """从数据库加载股票列表"""
        try:
            database_path = settings.get_database_path()
            conn = sqlite3.connect(database_path)
            df = pd.read_sql_query("SELECT code, name, market FROM stock_list", conn)
            conn.close()
            if not df.empty:
                return df
            return None
        except Exception as e:
            logger.debug(f"从数据库加载股票列表失败: {e}")
            return None
    
    def _save_to_database(self, df: pd.DataFrame) -> None:
        """保存股票列表到数据库"""
        try:
            from datetime import datetime
            database_path = settings.get_database_path()
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            
            # 清空旧数据
            cursor.execute("DELETE FROM stock_list")
            
            # 插入新数据
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for _, row in df.iterrows():
                cursor.execute(
                    "INSERT OR REPLACE INTO stock_list (code, name, market, update_time) VALUES (?, ?, ?, ?)",
                    (row["code"], row["name"], row["market"], update_time)
                )
            
            conn.commit()
            conn.close()
            logger.debug(f"股票列表已保存到数据库，共 {len(df)} 只股票")
        except Exception as e:
            logger.error(f"保存股票列表到数据库失败: {e}", exc_info=True)
    
    def clear_cache(self) -> None:
        """清除股票列表缓存"""
        self._stock_list_cache = None
        logger.debug("股票列表缓存已清除")
