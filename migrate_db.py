import sqlite3
import os

db_path = '/home/oracle/.openclaw/workspace/library_system/library.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(members)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'photo_path' not in columns:
        print("Adding photo_path column to members table...")
        cursor.execute('ALTER TABLE members ADD COLUMN photo_path TEXT')
        conn.commit()
        print("Column photo_path added successfully.")
    else:
        print("Column photo_path already exists.")
        
    conn.close()
except Exception as e:
    print(f"Migration failed: {e}")
