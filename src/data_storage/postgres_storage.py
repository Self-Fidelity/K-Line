"""PostgreSQL 数据存储实现

使用 SQLAlchemy + psycopg2 连接池，提供高性能、线程安全的数据存储。
替代原有的 SQLiteStorage，解决并发锁竞争和逐条插入性能问题。
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime
import json

import pandas as pd
from sqlalchemy import (
    create_engine, text, Table, Column, Integer, String, Float,
    MetaData, Index, inspect, UniqueConstraint,
)
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from src.data_storage.storage import DataStorage
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PostgresStorage(DataStorage):
    """PostgreSQL 数据存储实现，带连接池"""

    # 连接池配置
    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 20
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 3600  # 1小时回收连接

    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = POOL_SIZE,
        max_overflow: int = MAX_OVERFLOW,
    ):
        """
        初始化 PostgreSQL 存储

        Args:
            database_url: PostgreSQL 连接 URL，如 postgresql://user:pass@host:5432/kline
                         如果为 None 则使用配置中的 URL
            pool_size: 连接池核心大小
            max_overflow: 连接池最大溢出数
        """
        self.database_url = database_url or settings.DATABASE_URL
        self._engine: Optional[Engine] = None
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._init_engine()
        self._init_tables()

    def _init_engine(self) -> None:
        """初始化 SQLAlchemy 引擎和连接池"""
        self._engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self._pool_size,
            max_overflow=self._max_overflow,
            pool_timeout=self.POOL_TIMEOUT,
            pool_recycle=self.POOL_RECYCLE,
            pool_pre_ping=True,  # 连接前检查有效性
            echo=False,
            # psycopg2 特定参数
            connect_args={
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000",  # 30秒语句超时
            },
        )
        logger.info(f"PostgreSQL 引擎初始化完成: pool_size={self._pool_size}")

    @contextmanager
    def _get_connection(self):
        """获取数据库连接上下文管理器"""
        if self._engine is None:
            raise RuntimeError("数据库引擎未初始化")
        conn = self._engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def _init_tables(self) -> None:
        """初始化数据库表结构"""
        metadata = MetaData()

        # 日K线数据表
        Table(
            "stock_daily_kline",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("stock_code", String(10), nullable=False, comment="股票代码"),
            Column("trade_date", String(8), nullable=False, comment="交易日期 YYYYMMDD"),
            Column("open", Float, nullable=False, comment="开盘价"),
            Column("close", Float, nullable=False, comment="收盘价"),
            Column("high", Float, nullable=False, comment="最高价"),
            Column("low", Float, nullable=False, comment="最低价"),
            Column("volume", Float, nullable=False, comment="成交量"),
            Column("amount", Float, comment="成交额"),
            Column("pct_chg", Float, comment="涨跌幅"),
            Column("change", Float, comment="涨跌额"),
            Column("turnover", Float, comment="换手率"),
            Column("update_time", String(20), nullable=False, comment="更新时间"),
            UniqueConstraint("stock_code", "trade_date", name="uq_stock_date"),
        )

        # 策略参数表（旧版，保留向后兼容）
        Table(
            "stock_strategy_params",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("stock_code", String(10), nullable=False),
            Column("strategy_name", String(100), nullable=False),
            Column("params", String, nullable=False),
            Column("update_time", String(20), nullable=False),
            UniqueConstraint("stock_code", "strategy_name", name="uq_strategy_params"),
        )

        # 策略参数集表
        Table(
            "strategy_param_sets",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("stock_code", String(10), nullable=False),
            Column("strategy_name", String(100), nullable=False),
            Column("name", String(200), nullable=False),
            Column("description", String, default=""),
            Column("params", String, nullable=False),
            Column("param_ranges", String),
            Column("target_metric", String(50)),
            Column("best_score", Float),
            Column("optimization_method", String(50)),
            Column("num_particles", Integer),
            Column("max_iter", Integer),
            Column("date_range", String(100)),
            Column("created_at", String(20), nullable=False),
            Column("is_default", Integer, default=0),
            UniqueConstraint("stock_code", "strategy_name", "name", name="uq_param_set"),
        )

        # 聚合方案表
        Table(
            "aggregation_schemes",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("name", String(200), nullable=False, unique=True),
            Column("description", String, default=""),
            Column("strategies", String, nullable=False),
            Column("weights", String, nullable=False),
            Column("buy_threshold", Float, default=0.5),
            Column("sell_threshold", Float, default=-0.5),
            Column("created_at", String(20), nullable=False),
            Column("updated_at", String(20)),
        )

        # 用户表
        Table(
            "users",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("username", String(50), nullable=False, unique=True),
            Column("password_hash", String(255), nullable=False),
            Column("email", String(255)),
            Column("role", String(20), default="user"),
            Column("is_active", Integer, default=1),
            Column("created_at", String(20), nullable=False),
            Column("updated_at", String(20)),
        )

        # 自定义策略表
        Table(
            "custom_strategies",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("user_id", Integer, nullable=False),
            Column("name", String(200), nullable=False),
            Column("description", String, default=""),
            Column("detailed_description", String, default=""),
            Column("code", String, nullable=False),
            Column("parameter_descriptions", String, default="{}"),
            Column("file_path", String(500)),
            Column("is_public", Integer, default=0),
            Column("is_system", Integer, default=0),
            Column("created_at", String(20), nullable=False),
            Column("updated_at", String(20)),
        )

        # 审计日志表
        Table(
            "audit_logs",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("username", String(100), nullable=False),
            Column("action", String(200), nullable=False),
            Column("details", String),
            Column("ip_address", String(50)),
            Column("created_at", String(20), nullable=False),
        )

        # 自选股表
        Table(
            "watchlist",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("user_id", Integer, nullable=False),
            Column("stock_code", String(10), nullable=False),
            Column("stock_name", String(100)),
            Column("notes", String(500)),
            Column("created_at", String(20), nullable=False),
            UniqueConstraint("user_id", "stock_code", name="uq_watchlist_user_stock"),
        )
        )

        with self._get_connection() as conn:
            metadata.create_all(conn, checkfirst=True)

            # 创建索引
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_kline_stock_code ON stock_daily_kline(stock_code)",
                "CREATE INDEX IF NOT EXISTS idx_kline_trade_date ON stock_daily_kline(trade_date)",
                "CREATE INDEX IF NOT EXISTS idx_kline_stock_date ON stock_daily_kline(stock_code, trade_date)",
                "CREATE INDEX IF NOT EXISTS idx_param_sets_stock_strategy ON strategy_param_sets(stock_code, strategy_name)",
                "CREATE INDEX IF NOT EXISTS idx_param_sets_created ON strategy_param_sets(created_at DESC)",
            ]
            for idx_sql in indexes:
                conn.execute(text(idx_sql))
            conn.commit()

        logger.info("PostgreSQL 表结构初始化完成")

    # ───────────────────── 核心数据操作 ─────────────────────

    def save_daily_data(
        self,
        data: pd.DataFrame,
        stock_code: str,
    ) -> bool:
        """批量保存日K线数据（使用 executemany 模式）"""
        if data.empty:
            logger.warning(f"股票 {stock_code} 的数据为空，跳过保存")
            return False

        required_columns = ["date", "open", "close", "high", "low", "volume"]
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"数据缺少必要的列: {required_columns}")

        df = data.copy()
        df["stock_code"] = stock_code
        df["trade_date"] = df["date"].dt.strftime("%Y%m%d")
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 构建批量插入参数
        records = []
        for _, row in df.iterrows():
            records.append({
                "stock_code": stock_code,
                "trade_date": row["trade_date"],
                "open": float(row["open"]),
                "close": float(row["close"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "volume": float(row["volume"]),
                "amount": float(row.get("amount", 0)) if pd.notna(row.get("amount")) else None,
                "pct_chg": float(row.get("pct_chg", 0)) if pd.notna(row.get("pct_chg")) else None,
                "change": float(row.get("change", 0)) if pd.notna(row.get("change")) else None,
                "turnover": float(row.get("turnover", 0)) if pd.notna(row.get("turnover")) else None,
                "update_time": update_time,
            })

        with self._get_connection() as conn:
            insert_sql = text("""
                INSERT INTO stock_daily_kline
                    (stock_code, trade_date, open, close, high, low, volume,
                     amount, pct_chg, change, turnover, update_time)
                VALUES
                    (:stock_code, :trade_date, :open, :close, :high, :low, :volume,
                     :amount, :pct_chg, :change, :turnover, :update_time)
                ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                    open = EXCLUDED.open,
                    close = EXCLUDED.close,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    volume = EXCLUDED.volume,
                    amount = EXCLUDED.amount,
                    pct_chg = EXCLUDED.pct_chg,
                    change = EXCLUDED.change,
                    turnover = EXCLUDED.turnover,
                    update_time = EXCLUDED.update_time
            """)
            conn.execute(insert_sql, records)
            conn.commit()

        logger.info(f"股票 {stock_code} 保存了 {len(records)} 条数据")
        return True

    def get_daily_data(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """获取日K线数据"""
        with self._get_connection() as conn:
            query = """
                SELECT stock_code, trade_date, open, close, high, low,
                       volume, amount, pct_chg, change, turnover
                FROM stock_daily_kline
                WHERE stock_code = :stock_code
            """
            params = {"stock_code": stock_code}

            if start_date:
                query += " AND trade_date >= :start_date"
                params["start_date"] = start_date
            if end_date:
                query += " AND trade_date <= :end_date"
                params["end_date"] = end_date

            query += " ORDER BY trade_date ASC"

            df = pd.read_sql_query(text(query), conn, params=params)

            if not df.empty:
                df["date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
                df = df.drop(columns=["trade_date"], errors="ignore")

            return df

    def get_latest_date(self, stock_code: str) -> Optional[str]:
        """获取指定股票的最新数据日期"""
        with self._get_connection() as conn:
            result = conn.execute(
                text("SELECT MAX(trade_date) AS latest_date FROM stock_daily_kline WHERE stock_code = :code"),
                {"code": stock_code},
            ).fetchone()
            return result[0] if result and result[0] else None

    def get_all_latest_dates(self) -> dict[str, Optional[str]]:
        """批量获取所有股票的最新数据日期（单次查询，避免 N+1）"""
        with self._get_connection() as conn:
            rows = conn.execute(
                text(
                    "SELECT stock_code, MAX(trade_date) AS latest_date "
                    "FROM stock_daily_kline GROUP BY stock_code"
                )
            ).fetchall()
            return {row[0]: row[1] for row in rows} if rows else {}

    def check_data_exists(self, stock_code: str, trade_date: str) -> bool:
        """检查指定日期的数据是否存在"""
        with self._get_connection() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM stock_daily_kline "
                    "WHERE stock_code = :code AND trade_date = :date"
                ),
                {"code": stock_code, "date": trade_date},
            ).scalar()
            return result > 0

    def get_all_stocks(self) -> List[str]:
        """获取数据库中所有股票代码列表"""
        with self._get_connection() as conn:
            rows = conn.execute(
                text("SELECT DISTINCT stock_code FROM stock_daily_kline ORDER BY stock_code")
            ).fetchall()
            return [row[0] for row in rows]

    # ───────────────────── 策略参数操作 ─────────────────────

    def save_strategy_params(
        self, stock_code: str, strategy_name: str, params: str
    ) -> bool:
        """保存策略参数"""
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            conn.execute(
                text("""
                    INSERT INTO stock_strategy_params
                        (stock_code, strategy_name, params, update_time)
                    VALUES (:stock_code, :strategy_name, :params, :update_time)
                    ON CONFLICT (stock_code, strategy_name) DO UPDATE SET
                        params = EXCLUDED.params,
                        update_time = EXCLUDED.update_time
                """),
                {
                    "stock_code": stock_code,
                    "strategy_name": strategy_name,
                    "params": params,
                    "update_time": update_time,
                },
            )
            conn.commit()
        logger.info(f"保存策略参数成功: {stock_code}/{strategy_name}")
        return True

    def get_strategy_params(
        self, stock_code: str, strategy_name: str
    ) -> Optional[str]:
        """获取策略参数"""
        with self._get_connection() as conn:
            result = conn.execute(
                text(
                    "SELECT params FROM stock_strategy_params "
                    "WHERE stock_code = :code AND strategy_name = :name"
                ),
                {"code": stock_code, "name": strategy_name},
            ).fetchone()
            return result[0] if result else None

    # ───────────────────── 参数集操作 ─────────────────────

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
        is_default: bool = False,
    ) -> Optional[int]:
        """保存参数集"""
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            if is_default:
                conn.execute(
                    text(
                        "UPDATE strategy_param_sets SET is_default = 0 "
                        "WHERE stock_code = :code AND strategy_name = :name"
                    ),
                    {"code": stock_code, "name": strategy_name},
                )

            result = conn.execute(
                text("""
                    INSERT INTO strategy_param_sets
                        (stock_code, strategy_name, name, description, params,
                         param_ranges, target_metric, best_score, optimization_method,
                         num_particles, max_iter, date_range, created_at, is_default)
                    VALUES (:stock_code, :strategy_name, :name, :description, :params,
                            :param_ranges, :target_metric, :best_score, :optimization_method,
                            :num_particles, :max_iter, :date_range, :created_at, :is_default)
                    ON CONFLICT (stock_code, strategy_name, name) DO UPDATE SET
                        description = EXCLUDED.description,
                        params = EXCLUDED.params,
                        param_ranges = EXCLUDED.param_ranges,
                        target_metric = EXCLUDED.target_metric,
                        best_score = EXCLUDED.best_score,
                        optimization_method = EXCLUDED.optimization_method,
                        num_particles = EXCLUDED.num_particles,
                        max_iter = EXCLUDED.max_iter,
                        date_range = EXCLUDED.date_range,
                        created_at = EXCLUDED.created_at,
                        is_default = EXCLUDED.is_default
                    RETURNING id
                """),
                {
                    "stock_code": stock_code,
                    "strategy_name": strategy_name,
                    "name": name,
                    "description": description,
                    "params": json.dumps(params),
                    "param_ranges": json.dumps(param_ranges) if param_ranges else None,
                    "target_metric": target_metric,
                    "best_score": best_score,
                    "optimization_method": optimization_method,
                    "num_particles": num_particles,
                    "max_iter": max_iter,
                    "date_range": date_range,
                    "created_at": created_at,
                    "is_default": 1 if is_default else 0,
                },
            )
            conn.commit()
            param_set_id = result.fetchone()[0]
            logger.info(f"保存参数集成功: {stock_code}/{strategy_name}/{name}, ID={param_set_id}")
            return param_set_id

    def get_param_sets(
        self, stock_code: str, strategy_name: str
    ) -> List[Dict[str, Any]]:
        """获取参数集列表"""
        with self._get_connection() as conn:
            rows = conn.execute(
                text(
                    "SELECT * FROM strategy_param_sets "
                    "WHERE stock_code = :code AND strategy_name = :name "
                    "ORDER BY is_default DESC, created_at DESC"
                ),
                {"code": stock_code, "name": strategy_name},
            ).fetchall()

            results = []
            for row in rows:
                row_dict = dict(row._mapping)
                row_dict["params"] = json.loads(row_dict["params"])
                if row_dict.get("param_ranges"):
                    row_dict["param_ranges"] = json.loads(row_dict["param_ranges"])
                results.append(row_dict)
            return results

    def get_param_set_by_id(self, param_set_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取参数集"""
        with self._get_connection() as conn:
            row = conn.execute(
                text("SELECT * FROM strategy_param_sets WHERE id = :id"),
                {"id": param_set_id},
            ).fetchone()
            if row:
                row_dict = dict(row._mapping)
                row_dict["params"] = json.loads(row_dict["params"])
                if row_dict.get("param_ranges"):
                    row_dict["param_ranges"] = json.loads(row_dict["param_ranges"])
                return row_dict
            return None

    def delete_param_set(self, param_set_id: int) -> bool:
        """删除参数集"""
        with self._get_connection() as conn:
            conn.execute(
                text("DELETE FROM strategy_param_sets WHERE id = :id"),
                {"id": param_set_id},
            )
            conn.commit()
        logger.info(f"删除参数集成功: {param_set_id}")
        return True

    # ───────────────────── 聚合方案操作 ─────────────────────

    def save_aggregation_scheme(
        self,
        name: str,
        strategies: str,
        weights: str,
        description: str = "",
        buy_threshold: float = 0.5,
        sell_threshold: float = -0.5,
    ) -> Optional[int]:
        """保存聚合方案"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO aggregation_schemes
                        (name, description, strategies, weights, buy_threshold,
                         sell_threshold, created_at, updated_at)
                    VALUES (:name, :description, :strategies, :weights, :buy_threshold,
                            :sell_threshold, :created_at, :updated_at)
                    ON CONFLICT (name) DO UPDATE SET
                        description = EXCLUDED.description,
                        strategies = EXCLUDED.strategies,
                        weights = EXCLUDED.weights,
                        buy_threshold = EXCLUDED.buy_threshold,
                        sell_threshold = EXCLUDED.sell_threshold,
                        updated_at = EXCLUDED.updated_at
                    RETURNING id
                """),
                {
                    "name": name,
                    "description": description,
                    "strategies": strategies,
                    "weights": weights,
                    "buy_threshold": buy_threshold,
                    "sell_threshold": sell_threshold,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            conn.commit()
            return result.fetchone()[0]

    def get_aggregation_schemes(self) -> List[Dict[str, Any]]:
        """获取所有聚合方案"""
        with self._get_connection() as conn:
            rows = conn.execute(
                text("SELECT * FROM aggregation_schemes ORDER BY created_at DESC")
            ).fetchall()
            return [dict(row._mapping) for row in rows]

    def get_aggregation_scheme_by_id(self, scheme_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取聚合方案"""
        with self._get_connection() as conn:
            row = conn.execute(
                text("SELECT * FROM aggregation_schemes WHERE id = :id"),
                {"id": scheme_id},
            ).fetchone()
            return dict(row._mapping) if row else None

    def delete_aggregation_scheme(self, scheme_id: int) -> bool:
        """删除聚合方案"""
        with self._get_connection() as conn:
            conn.execute(
                text("DELETE FROM aggregation_schemes WHERE id = :id"),
                {"id": scheme_id},
            )
            conn.commit()
        return True

    # ───────────────────── 自定义策略操作 ─────────────────────

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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO custom_strategies
                        (user_id, name, description, detailed_description, code,
                         parameter_descriptions, file_path, is_public, created_at)
                    VALUES (:user_id, :name, :description, :detailed_description, :code,
                            :param_descs, :file_path, :is_public, :created_at)
                    RETURNING id
                """),
                {
                    "user_id": user_id,
                    "name": name,
                    "description": description,
                    "detailed_description": detailed_description,
                    "code": code,
                    "param_descs": json.dumps(parameter_descriptions or {}, ensure_ascii=False),
                    "file_path": file_path,
                    "is_public": 1 if is_public else 0,
                    "created_at": now,
                },
            )
            conn.commit()
            return result.fetchone()[0]

    def get_custom_strategy(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """获取单个自定义策略"""
        with self._get_connection() as conn:
            row = conn.execute(
                text("SELECT * FROM custom_strategies WHERE id = :id"),
                {"id": strategy_id},
            ).fetchone()
            if row:
                data = dict(row._mapping)
                data["parameter_descriptions"] = json.loads(data.get("parameter_descriptions", "{}"))
                return data
            return None

    def get_custom_strategy_by_user(
        self, strategy_id: int, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取用户拥有的策略"""
        with self._get_connection() as conn:
            row = conn.execute(
                text("SELECT * FROM custom_strategies WHERE id = :id AND user_id = :uid"),
                {"id": strategy_id, "uid": user_id},
            ).fetchone()
            if row:
                data = dict(row._mapping)
                data["parameter_descriptions"] = json.loads(data.get("parameter_descriptions", "{}"))
                return data
            return None

    def update_custom_strategy(
        self,
        strategy_id: int,
        **fields: Any,
    ) -> bool:
        """更新自定义策略字段"""
        if not fields:
            return False
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields["updated_at"] = now
        set_clause = ", ".join(f"{k} = :{k}" for k in fields)
        fields["id"] = strategy_id
        with self._get_connection() as conn:
            conn.execute(
                text(f"UPDATE custom_strategies SET {set_clause} WHERE id = :id"),
                fields,
            )
            conn.commit()
        return True

    def delete_custom_strategy(self, strategy_id: int) -> bool:
        """删除自定义策略"""
        with self._get_connection() as conn:
            conn.execute(
                text("DELETE FROM custom_strategies WHERE id = :id"),
                {"id": strategy_id},
            )
            conn.commit()
        return True

    def list_custom_strategies(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出所有自定义策略"""
        with self._get_connection() as conn:
            query = """
                SELECT cs.*, u.username
                FROM custom_strategies cs
                LEFT JOIN users u ON cs.user_id = u.id
            """
            params = {}
            if user_id is not None:
                query += " WHERE cs.user_id = :uid"
                params["uid"] = user_id
            query += " ORDER BY cs.created_at DESC"

            rows = conn.execute(text(query), params).fetchall()
            results = []
            for row in rows:
                data = dict(row._mapping)
                data["parameter_descriptions"] = json.loads(data.get("parameter_descriptions", "{}"))
                results.append(data)
            return results

    # ───────────────────── 用户操作 ─────────────────────

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        with self._get_connection() as conn:
            row = conn.execute(
                text("SELECT * FROM users WHERE username = :un"),
                {"un": username},
            ).fetchone()
            return dict(row._mapping) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        with self._get_connection() as conn:
            row = conn.execute(
                text("SELECT * FROM users WHERE id = :id"),
                {"id": user_id},
            ).fetchone()
            return dict(row._mapping) if row else None

    def create_user(
        self,
        username: str,
        password_hash: str,
        email: Optional[str] = None,
        role: str = "user",
    ) -> int:
        """创建用户，返回ID"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO users (username, password_hash, email, role, created_at)
                    VALUES (:un, :ph, :email, :role, :now)
                    RETURNING id
                """),
                {"un": username, "ph": password_hash, "email": email, "role": role, "now": now},
            )
            conn.commit()
            return result.fetchone()[0]

    def list_users(self) -> List[Dict[str, Any]]:
        """列出所有用户"""
        with self._get_connection() as conn:
            rows = conn.execute(
                text("SELECT id, username, email, role, is_active, created_at FROM users ORDER BY id")
            ).fetchall()
            return [dict(row._mapping) for row in rows]

    def update_user(self, user_id: int, **fields: Any) -> bool:
        """更新用户字段"""
        if not fields:
            return False
        fields["id"] = user_id
        set_clause = ", ".join(f"{k} = :{k}" for k in fields)
        with self._get_connection() as conn:
            conn.execute(
                text(f"UPDATE users SET {set_clause} WHERE id = :id"),
                fields,
            )
            conn.commit()
        return True

    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        with self._get_connection() as conn:
            conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
            conn.commit()
        return True

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
        with self._get_connection() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO audit_logs (username, action, details, ip_address, created_at)
                    VALUES (:un, :action, :details, :ip, :now)
                    RETURNING id
                """),
                {"un": username, "action": action, "details": details, "ip": ip_address, "now": now},
            )
            conn.commit()
            return result.fetchone()[0]

    def list_audit_logs(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出审计日志"""
        with self._get_connection() as conn:
            rows = conn.execute(
                text("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT :lim OFFSET :off"),
                {"lim": limit, "off": offset},
            ).fetchall()
            return [dict(row._mapping) for row in rows]

    # ───────────────────── 自选股 ─────────────────────

    def add_to_watchlist(
        self, user_id: int, stock_code: str, stock_name: Optional[str] = None
    ) -> int:
        """添加到自选股"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO watchlist (user_id, stock_code, stock_name, created_at)
                    VALUES (:uid, :code, :name, :now)
                    ON CONFLICT (user_id, stock_code) DO NOTHING
                    RETURNING id
                """),
                {"uid": user_id, "code": stock_code, "name": stock_name, "now": now},
            )
            conn.commit()
            row = result.fetchone()
            return row[0] if row else -1

    def remove_from_watchlist(self, user_id: int, stock_code: str) -> bool:
        """从自选股删除"""
        with self._get_connection() as conn:
            conn.execute(
                text("DELETE FROM watchlist WHERE user_id = :uid AND stock_code = :code"),
                {"uid": user_id, "code": stock_code},
            )
            conn.commit()
        return True

    def get_watchlist(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户自选股列表"""
        with self._get_connection() as conn:
            rows = conn.execute(
                text("SELECT * FROM watchlist WHERE user_id = :uid ORDER BY created_at DESC"),
                {"uid": user_id},
            ).fetchall()
            return [dict(row._mapping) for row in rows]

    def is_in_watchlist(self, user_id: int, stock_code: str) -> bool:
        """检查是否在自选股中"""
        with self._get_connection() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM watchlist "
                    "WHERE user_id = :uid AND stock_code = :code"
                ),
                {"uid": user_id, "code": stock_code},
            ).scalar()
            return result > 0

    # ───────────────────── 工具方法 ─────────────────────

    def close(self) -> None:
        """关闭连接池"""
        if self._engine:
            self._engine.dispose()
            logger.info("PostgreSQL 连接池已关闭")

    def health_check(self) -> bool:
        """健康检查"""
        try:
            with self._get_connection() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"PostgreSQL 健康检查失败: {e}")
            return False
