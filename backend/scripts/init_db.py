"""初始化数据库表结构"""

import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from backend.app.config import settings
from backend.app.utils.security import get_password_hash
from datetime import datetime, timezone
import sqlite3


def init_database():
    """初始化数据库表结构"""
    # 确保数据库目录存在
    settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(settings.DATABASE_PATH))
    cursor = conn.cursor()
    
    try:
        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                max_watchlist_count INTEGER DEFAULT 20,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        
        # 创建用户设置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                notification_email TEXT,
                notification_enabled BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 创建自定义策略表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                detailed_description TEXT,
                code TEXT NOT NULL,
                parameter_descriptions TEXT,
                file_path TEXT,
                is_public BOOLEAN DEFAULT 0,
                promoted_at TEXT,
                promoted_by INTEGER,
                is_system BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                UNIQUE(user_id, name),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 创建自选股票表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stock_code TEXT NOT NULL,
                period TEXT NOT NULL DEFAULT '1',
                created_at TEXT NOT NULL,
                updated_at TEXT,
                UNIQUE(user_id, stock_code),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 创建监控警报表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitor_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stock_code TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                strategy_params TEXT,
                alert_condition TEXT NOT NULL,
                alert_value REAL,
                is_active BOOLEAN DEFAULT 1,
                last_triggered_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 创建警报历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL,
                triggered_at TEXT NOT NULL,
                message TEXT,
                FOREIGN KEY (alert_id) REFERENCES monitor_alerts(id)
            )
        """)
        
        # 创建分时K线数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_minute_kline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                trade_datetime TEXT NOT NULL,
                period TEXT NOT NULL,
                open REAL NOT NULL,
                close REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                volume REAL NOT NULL,
                amount REAL,
                update_time TEXT NOT NULL,
                UNIQUE(stock_code, trade_datetime, period)
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_minute_stock_code 
            ON stock_minute_kline(stock_code)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_minute_datetime 
            ON stock_minute_kline(trade_datetime)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_minute_period 
            ON stock_minute_kline(period)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_minute_stock_datetime 
            ON stock_minute_kline(stock_code, trade_datetime, period)
        """)
        
        conn.commit()
        print("数据库表结构初始化完成！")
        
        # 创建默认管理员用户（如果不存在）
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            admin_password = get_password_hash("admin")  # 默认密码，生产环境应修改
            cursor.execute(
                "INSERT INTO users (username, email, hashed_password, role, max_watchlist_count, is_active, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    "admin",
                    "admin@example.com",
                    admin_password,
                    "admin",
                    100,
                    True,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
            print("默认管理员用户已创建 (username: admin, password: admin)")
        
    except Exception as e:
        conn.rollback()
        print(f"数据库初始化失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
