
import sqlite3

db_path = '/home/oracle/.openclaw/workspace/library.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # เพิ่มคอลัมน์ photo_path ในตาราง books
    try:
        cursor.execute("ALTER TABLE books ADD COLUMN photo_path TEXT")
        print("Successfully added photo_path column to books table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column photo_path already exists.")
        else:
            raise e
            
    conn.commit()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
