from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import date, datetime

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    books = relationship("Book", back_populates="category")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    isbn = Column(String, unique=True, index=True)
    book_type = Column(String, nullable=True) # เพิ่มประเภทหนังสือ
    category_id = Column(Integer, ForeignKey("categories.id"))
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    photo_path = Column(String, nullable=True)

    category = relationship("Category", back_populates="books")
    loans = relationship("Loan", back_populates="book")

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    student_id = Column(String, unique=True, index=True)
    student_class = Column(String)
    contact = Column(String)
    photo_path = Column(String, nullable=True)

    loans = relationship("Loan", back_populates="member")

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    borrow_date = Column(Date, default=date.today)
    due_date = Column(Date)
    return_date = Column(Date, nullable=True)
    is_returned = Column(Boolean, default=False)

    book = relationship("Book", back_populates="loans")
    member = relationship("Member", back_populates="loans")

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    action = Column(String)
    details = Column(String)
