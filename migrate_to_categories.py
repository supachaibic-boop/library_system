
import sqlite3
import os
import shutil

db_path = '/home/oracle/.openclaw/workspace/library.db'
backup_path = db_path + '.bak'

try:
    # Backup
    shutil.copy2(db_path, backup_path)
    print(f"Backup created at {backup_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Create categories table
    cursor.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)")
    
    # 2. Extract unique categories from books
    cursor.execute("SELECT DISTINCT category FROM books WHERE category IS NOT NULL AND category != ''")
    unique_categories = cursor.fetchall()
    
    for cat in unique_categories:
        try:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat[0],))
        except sqlite3.IntegrityError:
            pass # Category already exists

    # 3. Add category_id column to books
    try:
        cursor.execute("ALTER TABLE books ADD COLUMN category_id INTEGER REFERENCES categories(id)")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column category_id already exists.")
        else:
            raise e

    # 4. Update category_id based on existing category string
    cursor.execute("SELECT id, category FROM books")
    books = cursor.fetchall()
    
    for book_id, cat_name in books:
        if cat_name:
            cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
            cat_row = cursor.fetchone()
            if cat_row:
                cat_id = cat_row[0]
                cursor.execute("UPDATE books SET category_id = ? WHERE id = ?", (cat_id, book_id))

    # 5. (Optional) Remove old category column if SQLite version supports it
    # We will keep it for now just in case of rollback, or use a temporary table for migration
    # To truly remove it, we'd recreate the table. Let's just leave it to be safe for now.

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

except Exception as e:
    print(f"Error during migration: {e}")
    if os.path.exists(backup_path):
        print("Attempting to restore backup...")
        shutil.copy2(backup_path, db_path)
        print("Backup restored.")
