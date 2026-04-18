from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from library_system.database import SessionLocal, engine, Base
from library_system.models import Book, Member, Loan
from datetime import date

def test_db():
    print("Testing database connections...")
    db = SessionLocal()
    try:
        print("Checking Book count...")
        print(f"Total Books: {db.query(Book).count()}")
        
        print("Checking Member count...")
        print(f"Total Members: {db.query(Member).count()}")
        
        print("Checking Active Loans...")
        active_loans = db.query(Loan).filter(Loan.is_returned == False).all()
        print(f"Active Loans: {len(active_loans)}")
        
        print("Checking Overdue Loans...")
        today = date.today()
        overdue_loans = db.query(Loan).filter(Loan.is_returned == False, Loan.due_date < today).all()
        print(f"Overdue Loans: {len(overdue_loans)}")
        
        print("Database queries successful!")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_db()
