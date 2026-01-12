"""数据库迁移脚本：为 custom_strategies 表添加 code 字段"""

import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from src.config import settings
import sqlite3


def migrate():
    """执行迁移"""
    db_path = settings.get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查 code 字段是否已存在
        cursor.execute("PRAGMA table_info(custom_strategies)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'code' not in columns:
            print("添加 code 字段到 custom_strategies 表...")
            cursor.execute("""
                ALTER TABLE custom_strategies 
                ADD COLUMN code TEXT
            """)
            
            # 如果已有数据，从文件路径读取代码
            cursor.execute("SELECT id, file_path FROM custom_strategies WHERE code IS NULL")
            rows = cursor.fetchall()
            
            for row_id, file_path in rows:
                if file_path:
                    try:
                        code_file = Path(file_path)
                        if code_file.exists():
                            code = code_file.read_text(encoding='utf-8')
                            cursor.execute("""
                                UPDATE custom_strategies 
                                SET code = ? 
                                WHERE id = ?
                            """, (code, row_id))
                            print(f"  已为策略 ID {row_id} 添加代码")
                    except Exception as e:
                        print(f"  警告：无法读取策略 ID {row_id} 的代码文件: {e}")
            
            conn.commit()
            print("迁移完成：已添加 code 字段")
        else:
            print("code 字段已存在，跳过迁移")
        
        # 检查 detailed_description 字段
        if 'detailed_description' not in columns:
            print("添加 detailed_description 字段到 custom_strategies 表...")
            cursor.execute("""
                ALTER TABLE custom_strategies 
                ADD COLUMN detailed_description TEXT
            """)
            conn.commit()
            print("迁移完成：已添加 detailed_description 字段")
        else:
            print("detailed_description 字段已存在，跳过迁移")
        
        # 检查 parameter_descriptions 字段
        if 'parameter_descriptions' not in columns:
            print("添加 parameter_descriptions 字段到 custom_strategies 表...")
            cursor.execute("""
                ALTER TABLE custom_strategies 
                ADD COLUMN parameter_descriptions TEXT
            """)
            conn.commit()
            print("迁移完成：已添加 parameter_descriptions 字段")
        else:
            print("parameter_descriptions 字段已存在，跳过迁移")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
