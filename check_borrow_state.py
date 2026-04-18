from library_system.database import SessionLocal
from library_system.models import Book, Member, Loan

db = SessionLocal()
print("--- Books State ---")
books = db.query(Book).all()
for b in books:
    print(f"ID: {b.id}, Title: {b.title}, Total: {b.total_copies}, Available: {b.available_copies}")

print("\n--- Members State ---")
members = db.query(Member).all()
for m in members:
    print(f"ID: {m.id}, Name: {m.name}")

print("\n--- Active Loans ---")
loans = db.query(Loan).filter(Loan.is_returned == False).all()
for l in loans:
    print(f"Loan ID: {l.id}, Book ID: {l.book_id}, Member ID: {l.member_id}")

db.close()
