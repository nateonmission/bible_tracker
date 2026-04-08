# models/book.py

from sqlalchemy import Column, Integer, String
from database import Base  # your declarative base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    canon = Column(String(1), nullable=False)  # P, C, J
    testament = Column(String(2), nullable=False)  # OT, NT, AP
    chapter_count = Column(Integer, nullable=False)
    verse_count = Column(Integer, nullable=False)
    book_order = Column(Integer, nullable=False, index=True)