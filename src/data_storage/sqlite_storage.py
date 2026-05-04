"""SQLite 数据存储实现"""

from typing import Optional, List, Dict, Any
import sqlite3
import pandas as pd
import json
from datetime import datetime, timezone

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
            
            # 开启 WAL 模式以提高并发性能
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            
            # 检查是否需要迁移旧表结构（增加 data_source 列）
            cursor.execute("PRAGMA table_info(stock_daily_kline)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            if existing_columns and 'data_source' not in existing_columns:
                # 旧表迁移：重命名旧表 → 创建新表 → 导入数据 → 删除旧表
                logger.info("检测到旧版 stock_daily_kline 表，执行迁移...")
                cursor.execute("ALTER TABLE stock_daily_kline RENAME TO stock_daily_kline_old")
                
                # 创建新表（含 data_source）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stock_daily_kline (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stock_code TEXT NOT NULL,
                        trade_date TEXT NOT NULL,
                        data_source TEXT NOT NULL DEFAULT 'akshare',
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
                        UNIQUE(stock_code, trade_date, data_source)
                    )
                """)
                
                # 导入旧数据（默认标记为 akshare）
                cursor.execute("""
                    INSERT INTO stock_daily_kline 
                        (stock_code, trade_date, data_source, open, close, high, low, volume,
                         amount, pct_chg, change, turnover, update_time)
                    SELECT stock_code, trade_date, 'akshare', open, close, high, low, volume,
                           amount, pct_chg, change, turnover, update_time
                    FROM stock_daily_kline_old
                """)
                
                # 删除旧表
                cursor.execute("DROP TABLE stock_daily_kline_old")
                logger.info(f"表迁移完成，已导入 {cursor.rowcount} 条历史数据")
            else:
                # 直接创建新表（首次初始化）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stock_daily_kline (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stock_code TEXT NOT NULL,
                        trade_date TEXT NOT NULL,
                        data_source TEXT NOT NULL DEFAULT 'akshare',
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
                        UNIQUE(stock_code, trade_date, data_source)
                    )
                """)
            
            # 创建索引（先删除旧索引再重建，确保结构正确）
            cursor.execute("DROP INDEX IF EXISTS idx_stock_code")
            cursor.execute("DROP INDEX IF EXISTS idx_trade_date")
            cursor.execute("DROP INDEX IF EXISTS idx_stock_date")
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_kline_by_stock 
                ON stock_daily_kline(stock_code, data_source, trade_date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_kline_by_date 
                ON stock_daily_kline(trade_date, data_source, stock_code)
            """)

            # 创建策略参数表（旧版，保留向后兼容）
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
            
            # 创建策略参数集表（新版，支持多参数集）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_param_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    params TEXT NOT NULL,
                    param_ranges TEXT,
                    target_metric TEXT,
                    best_score REAL,
                    optimization_method TEXT,
                    num_particles INTEGER,
                    max_iter INTEGER,
                    date_range TEXT,
                    created_at TEXT NOT NULL,
                    is_default INTEGER DEFAULT 0,
                    UNIQUE(stock_code, strategy_name, name)
                )
            """)
            
            # 初始化策略聚合方案表
            self._init_aggregation_schemes_table(cursor)
            
            # 创建参数集索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_param_sets_stock_strategy
                ON strategy_param_sets(stock_code, strategy_name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_param_sets_created
                ON strategy_param_sets(created_at DESC)
            """)
            
            # 创建用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT,
                    hashed_password TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    max_watchlist_count INTEGER DEFAULT 20,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)

            # 创建审计日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # 创建自选股表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, stock_code)
                )
            """)

            # 创建数据更新配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_update_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 创建股票列表表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_list (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    market TEXT NOT NULL,
                    update_time TEXT NOT NULL
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
        data_source: str = "akshare",
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
            # 兼容字符串或 datetime 类型的 date 列
            if pd.api.types.is_datetime64_any_dtype(df["date"]):
                df["trade_date"] = df["date"].dt.strftime("%Y%m%d")
            else:
                df["trade_date"] = df["date"].astype(str)
            df["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 准备插入的数据
            records = []
            for _, row in df.iterrows():
                record = {
                    "stock_code": stock_code,
                    "trade_date": row["trade_date"],
                    "data_source": data_source,
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
            
            # 批量插入（使用 executemany 替代逐条插入，性能提升 50-100x）
            cursor = conn.cursor()
            insert_sql = """
                INSERT OR REPLACE INTO stock_daily_kline 
                (stock_code, trade_date, data_source, open, close, high, low, volume, 
                 amount, pct_chg, change, turnover, update_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # 准备批量参数列表
            batch_params = [
                (
                    record["stock_code"],
                    record["trade_date"],
                    record["data_source"],
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
                )
                for record in records
            ]

            cursor.executemany(insert_sql, batch_params)
            
            conn.commit()
            logger.info(f"股票 {stock_code} ({data_source}) 保存了 {len(records)} 条数据")
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
        data_source: Optional[str] = None,
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
            
            if data_source:
                query += " AND data_source = ?"
                params.append(data_source)
            
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
    
    def get_latest_date(self, stock_code: str, data_source: Optional[str] = None) -> Optional[str]:
        """
        获取指定股票的最新数据日期
        
        Args:
            stock_code: 股票代码
            data_source: 数据来源过滤，None 则查询所有来源
        
        Returns:
            最新日期字符串（格式：'20240101'），如果没有数据返回 None
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if data_source:
                cursor.execute(
                    "SELECT MAX(trade_date) as latest_date FROM stock_daily_kline WHERE stock_code = ? AND data_source = ?",
                    (stock_code, data_source),
                )
            else:
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

    def get_all_latest_dates(self, data_source: Optional[str] = None) -> dict:
        """批量获取所有股票的最新数据日期（单次查询，避免 N+1）"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if data_source:
                cursor.execute(
                    "SELECT stock_code, MAX(trade_date) as latest_date "
                    "FROM stock_daily_kline WHERE data_source = ? GROUP BY stock_code",
                    (data_source,)
                )
            else:
                cursor.execute(
                    "SELECT stock_code, MAX(trade_date) as latest_date "
                    "FROM stock_daily_kline GROUP BY stock_code"
                )
            rows = cursor.fetchall()
            return {row["stock_code"]: row["latest_date"] for row in rows} if rows else {}
        except Exception as e:
            logger.error(f"批量获取最新日期失败: {e}", exc_info=True)
            return {}
        finally:
            conn.close()

    def check_data_exists(
        self,
        stock_code: str,
        trade_date: str,
        data_source: str = "akshare",
    ) -> bool:
        """
        检查指定日期的数据是否存在
        
        Args:
            stock_code: 股票代码
            trade_date: 交易日期（格式：'20240101'）
            data_source: 数据来源
        
        Returns:
            如果数据存在返回 True，否则返回 False
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM stock_daily_kline WHERE stock_code = ? AND trade_date = ? AND data_source = ?",
                (stock_code, trade_date, data_source),
            )
            result = cursor.fetchone()
            return result["count"] > 0 if result else False
            
        except Exception as e:
            logger.error(f"检查数据是否存在失败: {e}", exc_info=True)
            return False
        finally:
            conn.close()
    
    def get_all_stocks(self, data_source: Optional[str] = None) -> list[str]:
        """
        获取数据库中所有股票代码列表
        
        Args:
            data_source: 数据来源过滤，None 则返回所有来源
        
        Returns:
            股票代码列表
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if data_source:
                cursor.execute(
                    "SELECT DISTINCT stock_code FROM stock_daily_kline WHERE data_source = ? ORDER BY stock_code",
                    (data_source,)
                )
            else:
                cursor.execute("SELECT DISTINCT stock_code FROM stock_daily_kline ORDER BY stock_code")
            results = cursor.fetchall()
            return [row["stock_code"] for row in results]
            
        except Exception as e:
            logger.error(f"获取所有股票代码失败: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    def clear_data_by_source(self, data_source: str) -> int:
        """
        清空指定数据来源的所有日K线数据
        
        Args:
            data_source: 数据来源，'akshare' 或 'tushare'
        
        Returns:
            删除的行数
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM stock_daily_kline WHERE data_source = ?",
                (data_source,)
            )
            deleted = cursor.rowcount
            conn.commit()
            logger.warning(f"已清空数据来源 {data_source} 的 {deleted} 条日K线数据")
            return deleted
        except Exception as e:
            logger.error(f"清空数据来源 {data_source} 数据失败: {e}", exc_info=True)
            conn.rollback()
            return 0
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

    # ==================== 参数集管理方法 ====================
    
    def save_param_set(
        self,
        stock_code: str,
        strategy_name: str,
        name: str,
        params: Dict[str, Any],
        description: str = "",
        param_ranges: Optional[Dict[str, List[float]]] = None,
        target_metric: Optional[str] = None,
        best_score: Optional[float] = None,
        optimization_method: Optional[str] = None,
        num_particles: Optional[int] = None,
        max_iter: Optional[int] = None,
        date_range: Optional[str] = None,
        is_default: bool = False
    ) -> Optional[int]:
        """
        保存参数集
        
        Args:
            stock_code: 股票代码
            strategy_name: 策略名称
            name: 参数集名称
            params: 参数字典
            description: 描述
            param_ranges: 参数范围
            target_metric: 优化目标指标
            best_score: 最佳得分
            optimization_method: 优化方法
            num_particles: 粒子数
            max_iter: 迭代次数
            date_range: 日期范围
            is_default: 是否为默认参数集
        
        Returns:
            参数集ID，失败返回None
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 如果设置为默认，先将其他参数集的默认标志清除
            if is_default:
                cursor.execute(
                    "UPDATE strategy_param_sets SET is_default = 0 WHERE stock_code = ? AND strategy_name = ?",
                    (stock_code, strategy_name)
                )
            
            sql = """
                INSERT OR REPLACE INTO strategy_param_sets
                (stock_code, strategy_name, name, description, params, param_ranges,
                 target_metric, best_score, optimization_method, num_particles, max_iter,
                 date_range, created_at, is_default)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(sql, (
                stock_code,
                strategy_name,
                name,
                description,
                json.dumps(params),
                json.dumps(param_ranges) if param_ranges else None,
                target_metric,
                best_score,
                optimization_method,
                num_particles,
                max_iter,
                date_range,
                created_at,
                1 if is_default else 0
            ))
            
            conn.commit()
            param_set_id = cursor.lastrowid
            logger.info(f"保存参数集成功: {stock_code}/{strategy_name}/{name}, ID={param_set_id}")
            return param_set_id
        
        except Exception as e:
            logger.error(f"保存参数集失败: {e}", exc_info=True)
            conn.rollback()
            return None
        finally:
            conn.close()

    def get_param_sets(
        self,
        stock_code: str,
        strategy_name: str
    ) -> List[Dict[str, Any]]:
        """
        获取参数集列表
        
        Args:
            stock_code: 股票代码
            strategy_name: 策略名称
        
        Returns:
            参数集列表
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM strategy_param_sets
                WHERE stock_code = ? AND strategy_name = ?
                ORDER BY is_default DESC, created_at DESC
                """,
                (stock_code, strategy_name)
            )
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # 解析JSON字段
                result['params'] = json.loads(result['params'])
                if result['param_ranges']:
                    result['param_ranges'] = json.loads(result['param_ranges'])
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"获取参数集失败: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    def get_param_set_by_id(self, param_set_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取参数集"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM strategy_param_sets WHERE id = ?",
                (param_set_id,)
            )
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['params'] = json.loads(result['params'])
                if result['param_ranges']:
                    result['param_ranges'] = json.loads(result['param_ranges'])
                return result
            return None
        
        except Exception as e:
            logger.error(f"获取参数集失败: {e}", exc_info=True)
            return None
        finally:
            conn.close()

    def delete_param_set(self, param_set_id: int) -> bool:
        """删除参数集"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM strategy_param_sets WHERE id = ?",
                (param_set_id,)
            )
            conn.commit()
            logger.info(f"删除参数集成功: {param_set_id}")
            return True
        
        except Exception as e:
            logger.error(f"删除参数集失败: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()

    def set_default_param_set(
        self,
        param_set_id: int,
        stock_code: str,
        strategy_name: str
    ) -> bool:
        """设置默认参数集"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 先清除所有默认标志
            cursor.execute(
                "UPDATE strategy_param_sets SET is_default = 0 WHERE stock_code = ? AND strategy_name = ?",
                (stock_code, strategy_name)
            )
            
            # 设置指定参数集为默认
            cursor.execute(
                "UPDATE strategy_param_sets SET is_default = 1 WHERE id = ?",
                (param_set_id,)
            )
            
            conn.commit()
            logger.info(f"设置默认参数集成功: {param_set_id}")
            return True
        
        except Exception as e:
            logger.error(f"设置默认参数集失败: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_default_param_set(
        self,
        stock_code: str,
        strategy_name: str
    ) -> Optional[Dict[str, Any]]:
        """获取默认参数集"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM strategy_param_sets
                WHERE stock_code = ? AND strategy_name = ? AND is_default = 1
                LIMIT 1
                """,
                (stock_code, strategy_name)
            )
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['params'] = json.loads(result['params'])
                if result['param_ranges']:
                    result['param_ranges'] = json.loads(result['param_ranges'])
                return result
            return None
        
        except Exception as e:
            logger.error(f"获取默认参数集失败: {e}", exc_info=True)
            return None
        finally:
            conn.close()

    # ==================== 策略聚合方案管理 ====================

    def _init_aggregation_schemes_table(self, cursor):
        """初始化策略聚合方案表"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aggregation_schemes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                stock_code TEXT,
                strategies TEXT NOT NULL,
                buy_threshold REAL NOT NULL,
                sell_threshold REAL NOT NULL,
                required_strategies TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agg_schemes_name 
            ON aggregation_schemes(name)
        """)

    def save_aggregation_scheme(
        self,
        name: str,
        strategies: List[Dict[str, Any]],
        buy_threshold: float,
        sell_threshold: float,
        required_strategies: List[str],
        description: str = "",
        stock_code: Optional[str] = None
    ) -> Optional[int]:
        """保存策略聚合方案"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            self._init_aggregation_schemes_table(cursor)
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            sql = """
                INSERT INTO aggregation_schemes
                (name, description, stock_code, strategies, buy_threshold, sell_threshold, 
                 required_strategies, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(sql, (
                name,
                description,
                stock_code,
                json.dumps(strategies),
                buy_threshold,
                sell_threshold,
                json.dumps(required_strategies),
                now,
                now
            ))
            
            conn.commit()
            scheme_id = cursor.lastrowid
            logger.info(f"保存聚合方案成功: {name}, ID={scheme_id}")
            return scheme_id
            
        except Exception as e:
            logger.error(f"保存聚合方案失败: {e}", exc_info=True)
            conn.rollback()
            return None
        finally:
            conn.close()

    def get_aggregation_schemes(self, stock_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取策略聚合方案列表"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            self._init_aggregation_schemes_table(cursor)
            
            sql = "SELECT * FROM aggregation_schemes"
            params = []
            
            if stock_code:
                sql += " WHERE stock_code = ? OR stock_code IS NULL"
                params.append(stock_code)
                
            sql += " ORDER BY created_at DESC"
            
            cursor.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['strategies'] = json.loads(result['strategies'])
                result['required_strategies'] = json.loads(result['required_strategies'])
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"获取聚合方案列表失败: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    def delete_aggregation_scheme(self, scheme_id: int) -> bool:
        """删除策略聚合方案"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM aggregation_schemes WHERE id = ?", (scheme_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"删除聚合方案失败: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()

    # ==================== 自定义策略管理 ====================

    def create_custom_strategy(
        self,
        user_id: int,
        name: str,
        code: str,
        description: str = "",
        detailed_description: str = "",
        parameter_descriptions: Optional[Dict[str, str]] = None,
        file_path: Optional[str] = None,
        is_public: bool = False,
    ) -> int:
        """创建自定义策略，返回策略ID"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # 确保表存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS custom_strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    detailed_description TEXT DEFAULT '',
                    code TEXT NOT NULL,
                    parameter_descriptions TEXT DEFAULT '{}',
                    file_path TEXT,
                    is_public INTEGER DEFAULT 0,
                    is_system INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            """)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO custom_strategies (user_id, name, description, detailed_description, code, parameter_descriptions, file_path, is_public, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, name, description, detailed_description, code,
                 json.dumps(parameter_descriptions or {}, ensure_ascii=False),
                 file_path, 1 if is_public else 0, now),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"创建自定义策略失败: {e}", exc_info=True)
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_custom_strategy(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """获取单个自定义策略"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM custom_strategies WHERE id = ?", (strategy_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result["parameter_descriptions"] = json.loads(result.get("parameter_descriptions", "{}"))
                return result
            return None
        except Exception as e:
            logger.error(f"获取自定义策略失败: {e}", exc_info=True)
            return None
        finally:
            conn.close()

    def get_custom_strategy_by_user(
        self, strategy_id: int, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取用户拥有的策略"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM custom_strategies WHERE id = ? AND user_id = ?",
                (strategy_id, user_id),
            )
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result["parameter_descriptions"] = json.loads(result.get("parameter_descriptions", "{}"))
                return result
            return None
        except Exception as e:
            logger.error(f"获取用户自定义策略失败: {e}", exc_info=True)
            return None
        finally:
            conn.close()

    def update_custom_strategy(self, strategy_id: int, **fields: Any) -> bool:
        """更新自定义策略字段"""
        if not fields:
            return False
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            fields["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            values = list(fields.values()) + [strategy_id]
            cursor.execute(f"UPDATE custom_strategies SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"更新自定义策略失败: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_custom_strategy(self, strategy_id: int) -> bool:
        """删除自定义策略"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM custom_strategies WHERE id = ?", (strategy_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"删除自定义策略失败: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()

    def list_custom_strategies(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出所有自定义策略"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # 确保 users 表存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT,
                    hashed_password TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    max_watchlist_count INTEGER DEFAULT 20,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)
            query = """
                SELECT cs.*, u.username
                FROM custom_strategies cs
                LEFT JOIN users u ON cs.user_id = u.id
            """
            params: list = []
            if user_id is not None:
                query += " WHERE cs.user_id = ?"
                params.append(user_id)
            query += " ORDER BY cs.created_at DESC"
            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                data["parameter_descriptions"] = json.loads(data.get("parameter_descriptions", "{}"))
                results.append(data)
            return results
        except Exception as e:
            logger.error(f"列出自定义策略失败: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    # ───────────────────── 用户管理 ─────────────────────

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, email, hashed_password, role,
                       max_watchlist_count, is_active, created_at
                FROM users WHERE username = ?
                """,
                (username,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, email, role,
                       max_watchlist_count, is_active, created_at
                FROM users WHERE id = ?
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def create_user(
        self,
        username: str,
        password_hash: str,
        email: Optional[str] = None,
        role: str = "user",
        max_watchlist_count: Optional[int] = None,
        is_active: bool = True,
    ) -> int:
        """创建用户，返回ID"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if max_watchlist_count is None:
            max_watchlist_count = 20
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, email, hashed_password, role,
                                   max_watchlist_count, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (username, email, password_hash, role,
                 max_watchlist_count, 1 if is_active else 0, now),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def check_email_exists(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        if not email:
            return False
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def list_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有用户"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, email, role,
                       max_watchlist_count, is_active, created_at
                FROM users
                ORDER BY id
                LIMIT ? OFFSET ?
                """,
                (limit, skip),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_user(self, user_id: int, **fields: Any) -> bool:
        """更新用户字段"""
        if not fields:
            return False
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            values = list(fields.values()) + [user_id]
            cursor.execute(
                f"UPDATE users SET {set_clause} WHERE id = ?",
                values,
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ───────────────────── 股票列表 ─────────────────────

    def init_stock_list_table(self) -> None:
        """初始化股票列表表（已在 _init_database 中创建）"""
        pass

    def load_stock_list(self) -> Optional[pd.DataFrame]:
        """从数据库加载股票列表"""
        try:
            conn = self._get_connection()
            df = pd.read_sql_query("SELECT code, name, market FROM stock_list", conn)
            conn.close()
            if not df.empty:
                return df
            return None
        except Exception as e:
            logger.debug(f"从数据库加载股票列表失败: {e}")
            return None

    def save_stock_list(self, df: pd.DataFrame) -> None:
        """保存股票列表到数据库（带事务保护）"""
        from datetime import datetime
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stock_list")
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for _, row in df.iterrows():
                cursor.execute(
                    "INSERT OR REPLACE INTO stock_list (code, name, market, update_time) VALUES (?, ?, ?, ?)",
                    (row["code"], row["name"], row["market"], update_time),
                )
            conn.commit()
            logger.debug(f"股票列表已保存到数据库，共 {len(df)} 只股票")
        except Exception as e:
            conn.rollback()
            logger.error(f"保存股票列表到数据库失败: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    # ───────────────────── 审计日志 ─────────────────────

    def create_audit_log(
        self,
        username: str,
        action: str,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> int:
        """创建审计日志"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (username, action, details, ip_address, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, action, details, ip_address, now),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def list_audit_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """列出审计日志"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # ───────────────────── 自选股 ─────────────────────

    def add_to_watchlist(
        self, user_id: int, stock_code: str, stock_name: Optional[str] = None
    ) -> int:
        """添加到自选股"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO watchlist (user_id, stock_code, stock_name, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, stock_code, stock_name, now),
            )
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else -1
        finally:
            conn.close()

    def remove_from_watchlist(self, user_id: int, stock_code: str) -> bool:
        """从自选股删除"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND stock_code = ?",
                (user_id, stock_code),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_watchlist(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户自选股列表"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT w.id, w.user_id, w.stock_code, s.name as stock_name, w.created_at
                FROM watchlist w
                LEFT JOIN stock_list s ON w.stock_code = s.code
                WHERE w.user_id = ?
                ORDER BY w.created_at DESC
                """,
                (user_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def is_in_watchlist(self, user_id: int, stock_code: str) -> bool:
        """检查是否在自选股中"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM watchlist WHERE user_id = ? AND stock_code = ?",
                (user_id, stock_code),
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    # ───────────────────── 数据更新配置 ─────────────────────

    def init_update_config_table(self) -> None:
        """初始化数据更新配置表（已在 _init_database 中创建）"""
        pass

    def get_update_config(self, key: str, default: str) -> str:
        """获取更新配置值"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM data_update_config WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()
            return row["value"] if row else default
        except Exception:
            return default
        finally:
            conn.close()

    def set_update_config(self, key: str, value: str) -> None:
        """设置更新配置值"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                """
                INSERT OR REPLACE INTO data_update_config (key, value, updated_at)
                VALUES (?, ?, ?)
                """,
                (key, value, now),
            )
            conn.commit()
        finally:
            conn.close()
