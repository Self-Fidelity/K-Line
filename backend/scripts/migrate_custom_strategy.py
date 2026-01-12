
import sqlite3
from pathlib import Path
import sys

# 添加 src 目录到路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from src.config import settings

def migrate():
    db_path = settings.DATABASE_PATH
    print(f"Migrating database at {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check columns
        cursor.execute("PRAGMA table_info(custom_strategies)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "detailed_description" not in columns:
            print("Adding detailed_description column...")
            cursor.execute("ALTER TABLE custom_strategies ADD COLUMN detailed_description TEXT DEFAULT ''")
            
        if "parameter_descriptions" not in columns:
            print("Adding parameter_descriptions column...")
            # Store as JSON string
            cursor.execute("ALTER TABLE custom_strategies ADD COLUMN parameter_descriptions TEXT DEFAULT '{}'")
            
        conn.commit()
        print("Migration completed successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
