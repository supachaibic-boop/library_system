import os
from fastapi import FastAPI, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Optional
import shutil
import uuid

from database import get_db, engine, Base
from models import Book, Member, Loan, Category, Log
from schemas import BookCreate, MemberCreate

app = FastAPI()

# Use absolute path for templates to prevent TemplateNotFound errors
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)

# Setup static files for member photos
static_dir = os.path.join(current_dir, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create database tables on startup
Base.metadata.create_all(bind=engine)

# --- Helper Functions ---
def create_log(db: Session, action: str, details: str):
    # Save to Database
    log = Log(action=action, details=details)
    db.add(log)
    db.commit()
    
    # Save to File (using absolute path to keep logs in the system folder)
    try:
        log_path = os.path.join(current_dir, "library_activity.log")
        with open(log_path, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            f.write(f"[{timestamp}] {action}: {details}\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

def get_overdue_loans(db: Session):
    today = date.today()
    return db.query(Loan).filter(Loan.is_returned == False, Loan.due_date < today).all()

# --- Routes ---

@app.get("/logs", response_class=HTMLResponse)
async def list_logs(request: Request, db: Session = Depends(get_db)):
    logs = db.query(Log).order_by(Log.timestamp.desc()).limit(30).all()
    return templates.TemplateResponse("logs.html", {"request": request, "logs": logs})

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    total_books = db.query(Book).count()
    total_members = db.query(Member).count()
    active_loans = db.query(Loan).filter(Loan.is_returned == False).all()
    overdue_loans = get_overdue_loans(db)
    
    # คำนวณจำนวนคนที่ยืม (Unique Members)
    borrower_ids = {loan.member_id for loan in active_loans}
    borrower_count = len(borrower_ids)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_books": total_books,
        "total_members": total_members,
        "active_loans": active_loans,
        "overdue_loans": overdue_loans,
        "borrower_count": borrower_count,
        "today": date.today()
    })

# --- Book Management ---

@app.get("/books", response_class=HTMLResponse)
async def list_books(request: Request, search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Book)
    if search:
        query = query.filter((Book.title.contains(search)) | (Book.author.contains(search)))
    books = query.all()
    return templates.TemplateResponse("books.html", {"request": request, "books": books, "search": search})

@app.get("/books/add", response_class=HTMLResponse)
async def add_book_page(request: Request, db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    # คำนวณ ID ถัดไป (Running Number)
    max_id = db.query(func.max(Book.id)).scalar() or 0
    next_id = max_id + 1
    return templates.TemplateResponse("add_book.html", {
        "request": request, 
        "categories": categories, 
        "next_id": next_id
    })

@app.post("/books/add")
async def add_book(
    title: str = Form(...), author: str = Form(...), isbn: str = Form(...),
    category_id: int = Form(...), total_copies: int = Form(1), 
    db: Session = Depends(get_db)
):
    book = Book(
        title=title, author=author, isbn=isbn, category_id=category_id,
        total_copies=total_copies, available_copies=total_copies
    )
    db.add(book)
    db.commit()
    
    category = db.query(Category).filter(Category.id == category_id).first()
    category_name = category.name if category else "Unknown"
    create_log(db, "เพิ่มหนังสือ", f"{title},{isbn},{category_name},{total_copies}")
    return RedirectResponse(url="/books", status_code=303)

@app.get("/books/edit/{book_id}", response_class=HTMLResponse)
async def edit_book_page(request: Request, book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    categories = db.query(Category).all()
    return templates.TemplateResponse("edit_book.html", {"request": request, "book": book, "categories": categories})

@app.post("/books/edit/{book_id}")
async def edit_book(
    book_id: int, title: str = Form(...), author: str = Form(...), 
    isbn: str = Form(...), category_id: int = Form(...), 
    total_copies: int = Form(...), photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
        
    book.title = title
    book.author = author
    book.isbn = isbn
    book.category_id = category_id
    book.total_copies = total_copies
    
    if photo and photo.filename:
        # จัดการรูปภาพหนังสือ
        if book.photo_path:
            old_photo_path = os.path.join(current_dir, "static", "books", book.photo_path)
            if os.path.exists(old_photo_path):
                os.remove(old_photo_path)

        ext = os.path.splitext(photo.filename)[1]
        photo_filename = f"{uuid.uuid4()}{ext}"
        photo_path = os.path.join(current_dir, "static", "books", photo_filename)
        
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        
        book.photo_path = photo_filename
    
    # แก้ไข Bug: คำนวณจำนวนหนังสือคงเหลือที่ถูกต้อง
    # นับจำนวนที่ถูกยืมและยังไม่ได้คืน
    current_loans_count = db.query(Loan).filter(
        Loan.book_id == book_id, 
        Loan.is_returned == False
    ).count()
    
    # จำนวนที่ว่าง = ทั้งหมด - จำนวนที่ถูกยืม
    book.available_copies = total_copies - current_loans_count
    
    # ป้องกันกรณีจำนวนที่ยืมมีมากกว่าจำนวนรวมที่ระบุใหม่ (ป้องกันติดลบ)
    if book.available_copies < 0:
        book.available_copies = 0
        
    db.commit()
    category = db.query(Category).filter(Category.id == book.category_id).first()
    category_name = category.name if category else "Unknown"
    create_log(db, "แก้ไขหนังสือ", f"{book_id},{title},{category_name},{total_copies}")
    return RedirectResponse(url="/books", status_code=303)

@app.get("/books/delete/{book_id}")
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    title = book.title if book else "Unknown"
    db.delete(book)
    db.commit()
    create_log(db, "ลบหนังสือ", f"{title},{book_id}")
    return RedirectResponse(url="/books", status_code=303)

# --- Category Management ---

@app.get("/categories", response_class=HTMLResponse)
async def list_categories(request: Request, db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return templates.TemplateResponse("categories.html", {"request": request, "categories": categories})

@app.get("/categories/add", response_class=HTMLResponse)
async def add_category_page(request: Request):
    return templates.TemplateResponse("add_category.html", {"request": request})

@app.post("/categories/add")
async def add_category(name: str = Form(...), db: Session = Depends(get_db)):
    # ตรวจสอบว่ามีหมวดหมู่นี้อยู่แล้วหรือไม่
    existing = db.query(Category).filter(Category.name == name).first()
    if existing:
        # ถ้ามีอยู่แล้วให้ redirect กลับไปหน้าลิสต์ (หรืออาจจะส่ง error message)
        return RedirectResponse(url="/categories", status_code=303)
    
    category = Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category) # เพื่อให้ได้ id ของ category ที่ถูกสร้าง
    create_log(db, "เพิ่มหมวดหมู่", f"{category.id},{name}")
    return RedirectResponse(url="/categories", status_code=303)

@app.get("/categories/edit/{category_id}", response_class=HTMLResponse)
async def edit_category_page(request: Request, category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return templates.TemplateResponse("edit_category.html", {"request": request, "category": category})

@app.post("/categories/edit/{category_id}")
async def edit_category(category_id: int, name: str = Form(...), db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # ตรวจสอบว่าชื่อใหม่ซ้ำกับหมวดหมู่อื่นหรือไม่ (ยกเว้นตัวมันเอง)
    existing = db.query(Category).filter(Category.name == name, Category.id != category_id).first()
    if existing:
        # ในกรณีที่ซ้ำ อาจจะส่ง error กลับไป หรือ redirect พร้อม message
        # สำหรับตอนนี้ขอกลับไปหน้าลิสต์ก่อนเพื่อให้ง่าย
        return RedirectResponse(url="/categories", status_code=303)
        
    category.name = name
    db.commit()
    create_log(db, "แก้ไขหมวดหมู่", f"{category_id},{name}")
    return RedirectResponse(url="/categories", status_code=303)

@app.get("/categories/delete/{category_id}")

async def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        name = category.name
        # เมื่อลบหมวดหมู่ หนังสือในหมวดนั้นจะถูก set category_id เป็น None (NULL)
        db.delete(category)
        db.commit()
        create_log(db, "ลบหมวดหมู่", f"{name},{category_id}")
    return RedirectResponse(url="/categories", status_code=303)

# --- Member Management ---

@app.get("/members", response_class=HTMLResponse)
async def list_members(request: Request, db: Session = Depends(get_db)):
    members = db.query(Member).all()
    return templates.TemplateResponse("members.html", {"request": request, "members": members})

@app.get("/members/add", response_class=HTMLResponse)
async def add_member_page(request: Request):
    return templates.TemplateResponse("add_member.html", {"request": request})

@app.post("/members/add")
async def add_member(
    name: str = Form(...), student_id: str = Form(...), 
    student_class: str = Form(...), contact: str = Form(...), 
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    photo_filename = None
    if photo:
        # สร้างชื่อไฟล์แบบสุ่มเพื่อป้องกันชื่อซ้ำ (UUID)
        ext = os.path.splitext(photo.filename)[1]
        photo_filename = f"{uuid.uuid4()}{ext}"
        photo_path = os.path.join(current_dir, "static", "members", photo_filename)
        
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

    member = Member(
        name=name, 
        student_id=student_id, 
        student_class=student_class, 
        contact=contact,
        photo_path=photo_filename # เก็บเฉพาะชื่อไฟล์ใน DB
    )
    db.add(member)
    db.commit()
    return RedirectResponse(url="/members", status_code=303)

@app.get("/members/edit/{member_id}", response_class=HTMLResponse)
async def edit_member_page(request: Request, member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return templates.TemplateResponse("edit_member.html", {"request": request, "member": member})

@app.post("/members/edit/{member_id}")
async def edit_member(
    member_id: int, name: str = Form(...), student_id: str = Form(...), 
    student_class: str = Form(...), contact: str = Form(...), 
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member.name = name
    member.student_id = student_id
    member.student_class = student_class
    member.contact = contact
    
    if photo and photo.filename:
        # จัดการรูปภาพใหม่
        # ลบรูปเก่าออกก่อนเพื่อไม่ให้เปลืองพื้นที่ Server
        if member.photo_path:
            old_photo_path = os.path.join(current_dir, "static", "members", member.photo_path)
            if os.path.exists(old_photo_path):
                os.remove(old_photo_path)

        ext = os.path.splitext(photo.filename)[1]
        photo_filename = f"{uuid.uuid4()}{ext}"
        photo_path = os.path.join(current_dir, "static", "members", photo_filename)
        
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        
        # อัปเดตชื่อไฟล์ใน DB
        member.photo_path = photo_filename
        
    db.commit()
    return RedirectResponse(url="/members", status_code=303)

@app.get("/members/delete/{member_id}")
async def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    db.delete(member)
    db.commit()
    return RedirectResponse(url="/members", status_code=303)

# --- Borrow & Return System ---

@app.get("/borrow", response_class=HTMLResponse)
async def borrow_page(request: Request, db: Session = Depends(get_db)):
    books = db.query(Book).filter(Book.available_copies > 0).all()
    members = db.query(Member).all()
    return templates.TemplateResponse("borrow.html", {"request": request, "books": books, "members": members})

@app.post("/borrow")
async def borrow_book(
    book_id: int = Form(...), member_id: int = Form(...), 
    due_date: date = Form(...), db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    member = db.query(Member).filter(Member.id == member_id).first()
    if book.available_copies <= 0:
        raise HTTPException(status_code=400, detail="Book not available")
    
    loan = Loan(book_id=book_id, member_id=member_id, due_date=due_date)
    book.available_copies -= 1
    
    db.add(loan)
    db.commit()
    
    borrow_date = date.today().strftime('%d-%m-%Y')
    due_date_str = due_date.strftime('%d-%m-%Y')
    create_log(db, "ยืมหนังสือ", f"{member.name},{book.title},{book.isbn},{borrow_date},{due_date_str}")
    return RedirectResponse(url="/", status_code=303)

@app.get("/return/{loan_id}")
async def return_book(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan or loan.is_returned:
        raise HTTPException(status_code=400, detail="Invalid loan")
    
    loan.is_returned = True
    loan.return_date = date.today()
    
    book = db.query(Book).filter(Book.id == loan.book_id).first()
    member = db.query(Member).filter(Member.id == loan.member_id).first()
    book.available_copies += 1
    
    db.commit()
    
    # คำนวณวันที่คืนสาย
    today = date.today()
    due_date = loan.due_date
    diff = (today - due_date).days
    overdue_days = diff if diff > 0 else 0
    status = "คืนสาย" if diff > 0 else "คืนตรงเวลา"
    
    due_date_str = due_date.strftime('%d-%m-%Y')
    create_log(db, "คืนหนังสือ", f"{member.name},{book.title},{book.isbn},{due_date_str},{status},{overdue_days}")
    return RedirectResponse(url="/", status_code=303)
