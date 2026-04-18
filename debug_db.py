
import sqlite3
import os

db_path = '/home/oracle/.openclaw/workspace/library.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(books)")
    columns = cursor.fetchall()
    print("Columns in 'books' table:")
    for col in columns:
        print(col)
    
    cursor.execute("SELECT * FROM books LIMIT 1")
    row = cursor.fetchone()
    print("\nSample row from 'books':")
    print(row)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
