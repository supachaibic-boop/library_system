from library_system.database import SessionLocal
from library_system.models import Book, Loan

db = SessionLocal()
try:
    books = db.query(Book).all()
    for book in books:
        # Count active loans for this book
        active_loans_count = db.query(Loan).filter(
            Loan.book_id == book.id, 
            Loan.is_returned == False
        ).count()
        
        # Correct the available copies
        new_available = book.total_copies - active_loans_count
        if new_available < 0:
            new_available = 0
            
        if book.available_copies != new_available:
            print(f"Updating Book ID {book.id} ({book.title}): {book.available_copies} -> {new_available}")
            book.available_copies = new_available
            
    db.commit()
    print("Database sync completed successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
