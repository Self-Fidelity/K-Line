"""SQLite 数据存储实现"""

from typing import Optional, List, Dict, Any
import sqlite3
import pandas as pd
import json
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
            
            # 开启 WAL 模式以提高并发性能
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            
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
            
            # 批量插入（使用 executemany 替代逐条插入，性能提升 50-100x）
            cursor = conn.cursor()
            insert_sql = """
                INSERT OR REPLACE INTO stock_daily_kline 
                (stock_code, trade_date, open, close, high, low, volume, 
                 amount, pct_chg, change, turnover, update_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # 准备批量参数列表
            batch_params = [
                (
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
                )
                for record in records
            ]

            cursor.executemany(insert_sql, batch_params)
            
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

    def get_all_latest_dates(self) -> dict:
        """批量获取所有股票的最新数据日期（单次查询，避免 N+1）"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
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
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    role TEXT DEFAULT 'user',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
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
