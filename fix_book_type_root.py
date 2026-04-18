import sqlite3

db_path = '/home/oracle/.openclaw/workspace/library.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add book_type column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE books ADD COLUMN book_type TEXT")
        print("Successfully added book_type column to books table in /home/oracle/.openclaw/workspace/library.db")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column book_type already exists.")
        else:
            raise e
            
    conn.commit()
    conn.close()
    print("Database fix completed.")
except Exception as e:
    print(f"Error: {e}")
