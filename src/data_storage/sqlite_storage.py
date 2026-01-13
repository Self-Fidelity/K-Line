"""SQLite 数据存储实现"""

from typing import Optional
import sqlite3
import pandas as pd
from datetime import datetime

from src.data_storage.storage import DataStorage
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SQLiteStorage(DataStorage):
    """SQLite 数据存储实现"""
    
    def __init__(self, database_path: Optional[str] = None):
        """
        初始化 SQLite 存储
        
        Args:
            database_path: 数据库文件路径，如果为 None 则使用配置中的路径
        """
        self.database_path = database_path or settings.get_database_path()
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self) -> None:
        """初始化数据库表结构"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 创建日K线数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_daily_kline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    open REAL NOT NULL,
                    close REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    volume REAL NOT NULL,
                    amount REAL,
                    pct_chg REAL,
                    change REAL,
                    turnover REAL,
                    update_time TEXT NOT NULL,
                    UNIQUE(stock_code, trade_date)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_code 
                ON stock_daily_kline(stock_code)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_date 
                ON stock_daily_kline(trade_date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_date 
                ON stock_daily_kline(stock_code, trade_date)
            """)

            # 创建策略参数表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_strategy_params (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    params TEXT NOT NULL,
                    update_time TEXT NOT NULL,
                    UNIQUE(stock_code, strategy_name)
                )
            """)
            
            conn.commit()
            logger.info(f"数据库初始化完成: {self.database_path}")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}", exc_info=True)
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def save_daily_data(
        self,
        data: pd.DataFrame,
        stock_code: str,
    ) -> bool:
        """
        保存日K线数据（支持增量更新，自动去重）
        
        Args:
            data: 日K线数据 DataFrame，必须包含列：date, open, close, high, low, volume
            stock_code: 股票代码
        
        Returns:
            是否保存成功
        """
        if data.empty:
            logger.warning(f"股票 {stock_code} 的数据为空，跳过保存")
            return False
        
        conn = self._get_connection()
        try:
            # 确保数据包含必要的列
            required_columns = ["date", "open", "close", "high", "low", "volume"]
            if not all(col in data.columns for col in required_columns):
                raise ValueError(f"数据缺少必要的列: {required_columns}")
            
            # 格式化数据
            df = data.copy()
            df["stock_code"] = stock_code
            df["trade_date"] = df["date"].dt.strftime("%Y%m%d")
            df["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 准备插入的数据
            records = []
            for _, row in df.iterrows():
                record = {
                    "stock_code": stock_code,
                    "trade_date": row["trade_date"],
                    "open": float(row["open"]),
                    "close": float(row["close"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "volume": float(row["volume"]),
                    "amount": float(row.get("amount", 0)) if "amount" in row else None,
                    "pct_chg": float(row.get("pct_chg", 0)) if "pct_chg" in row else None,
                    "change": float(row.get("change", 0)) if "change" in row else None,
                    "turnover": float(row.get("turnover", 0)) if "turnover" in row else None,
                    "update_time": row["update_time"],
                }
                records.append(record)
            
            # 使用 INSERT OR REPLACE 实现增量更新
            cursor = conn.cursor()
            insert_sql = """
                INSERT OR REPLACE INTO stock_daily_kline 
                (stock_code, trade_date, open, close, high, low, volume, 
                 amount, pct_chg, change, turnover, update_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            for record in records:
                cursor.execute(insert_sql, (
                    record["stock_code"],
                    record["trade_date"],
                    record["open"],
                    record["close"],
                    record["high"],
                    record["low"],
                    record["volume"],
                    record["amount"],
                    record["pct_chg"],
                    record["change"],
                    record["turnover"],
                    record["update_time"],
                ))
            
            conn.commit()
            logger.info(f"股票 {stock_code} 保存了 {len(records)} 条数据")
            return True
            
        except Exception as e:
            logger.error(f"保存股票 {stock_code} 数据失败: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()
    
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
        conn = self._get_connection()
        try:
            query = "SELECT * FROM stock_daily_kline WHERE stock_code = ?"
            params = [stock_code]
            
            if start_date:
                query += " AND trade_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND trade_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY trade_date ASC"
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                # 转换日期格式
                df["date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
                # 删除不需要的列
                df = df.drop(columns=["id", "update_time", "trade_date"], errors="ignore")
            
            return df
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 数据失败: {e}", exc_info=True)
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_latest_date(self, stock_code: str) -> Optional[str]:
        """
        获取指定股票的最新数据日期
        
        Args:
            stock_code: 股票代码
        
        Returns:
            最新日期字符串（格式：'20240101'），如果没有数据返回 None
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MAX(trade_date) as latest_date FROM stock_daily_kline WHERE stock_code = ?",
                (stock_code,),
            )
            result = cursor.fetchone()
            
            if result and result["latest_date"]:
                return result["latest_date"]
            return None
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 最新日期失败: {e}", exc_info=True)
            return None
        finally:
            conn.close()
    
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
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM stock_daily_kline WHERE stock_code = ? AND trade_date = ?",
                (stock_code, trade_date),
            )
            result = cursor.fetchone()
            return result["count"] > 0 if result else False
            
        except Exception as e:
            logger.error(f"检查数据是否存在失败: {e}", exc_info=True)
            return False
        finally:
            conn.close()
    
    def get_all_stocks(self) -> list[str]:
        """
        获取数据库中所有股票代码列表
        
        Returns:
            股票代码列表
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT stock_code FROM stock_daily_kline ORDER BY stock_code")
            results = cursor.fetchall()
            return [row["stock_code"] for row in results]
            
        except Exception as e:
            logger.error(f"获取所有股票代码失败: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    def save_strategy_params(
        self,
        stock_code: str,
        strategy_name: str,
        params: str,
    ) -> bool:
        """
        保存策略参数

        Args:
            stock_code: 股票代码
            strategy_name: 策略名称
            params: 参数 JSON 字符串

        Returns:
            是否保存成功
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            sql = """
                INSERT OR REPLACE INTO stock_strategy_params
                (stock_code, strategy_name, params, update_time)
                VALUES (?, ?, ?, ?)
            """

            cursor.execute(sql, (stock_code, strategy_name, params, update_time))
            conn.commit()
            logger.info(f"保存股票 {stock_code} 的 {strategy_name} 策略参数成功")
            return True

        except Exception as e:
            logger.error(f"保存策略参数失败: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_strategy_params(
        self,
        stock_code: str,
        strategy_name: str,
    ) -> Optional[str]:
        """
        获取策略参数

        Args:
            stock_code: 股票代码
            strategy_name: 策略名称

        Returns:
            参数 JSON 字符串，如果不存在返回 None
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT params FROM stock_strategy_params WHERE stock_code = ? AND strategy_name = ?",
                (stock_code, strategy_name),
            )
            result = cursor.fetchone()
            return result["params"] if result else None

        except Exception as e:
            logger.error(f"获取策略参数失败: {e}", exc_info=True)
            return None
        finally:
            conn.close()
