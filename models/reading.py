# models/reading.py

from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Reading(Base):
    __tablename__ = "readings"
    __table_args__ = (
        Index("ix_readings_date_read", "date_read"),
        Index("ix_readings_book_date", "book_id", "date_read"),
    )

    id = Column(Integer, primary_key=True, index=True)

    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)

    start_chapter = Column(Integer, nullable=False)
    start_verse = Column(Integer, nullable=False)

    end_chapter = Column(Integer, nullable=False)
    end_verse = Column(Integer, nullable=False)

    date_read = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship (optional but recommended)
    book = relationship("Book", backref="readings")
    
