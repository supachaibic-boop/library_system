from pydantic import BaseModel
from datetime import date
from typing import Optional

class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    category: str
    book_type: Optional[str] = None
    total_copies: int = 1
    available_copies: int = 1

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    category: Optional[str] = None
    book_type: Optional[str] = None
    total_copies: Optional[int] = None
    available_copies: Optional[int] = None

class BookResponse(BookBase):
    id: int
    class Config:
        from_attributes = True

class MemberBase(BaseModel):
    name: str
    student_id: str
    student_class: str
    contact: str

class MemberCreate(MemberBase):
    pass

class MemberResponse(MemberBase):
    id: int
    class Config:
        from_attributes = True

class LoanCreate(BaseModel):
    book_id: int
    member_id: int
    due_date: date

class LoanResponse(BaseModel):
    id: int
    book_id: int
    member_id: int
    borrow_date: date
    due_date: date
    return_date: Optional[date] = None
    is_returned: bool

    class Config:
        from_attributes = True
