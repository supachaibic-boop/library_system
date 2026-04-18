
import sqlite3

db_path = '/home/oracle/.openclaw/workspace/library.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for table in ['books', 'members']:
        print(f"\nChecking table: {table}")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
