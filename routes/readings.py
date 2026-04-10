from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models.book import Book
from models.reading import Reading
from schemas.reading import ReadingCreate, ReadingRead

router = APIRouter(prefix="/api/readings", tags=["readings"])


@router.post("/", response_model=ReadingRead, status_code=201)
def create_reading(
    reading: ReadingCreate,
    canon: str = Query(default="P"),
    db: Session = Depends(get_db),
):
    book = db.query(Book).filter(Book.id == reading.book_id, Book.canon == canon).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found in this canon")

    if reading.start_chapter > book.chapter_count:
        raise HTTPException(
            status_code=422,
            detail=f"{book.name} only has {book.chapter_count} chapters "
                   f"(start_chapter: {reading.start_chapter})",
        )
    if reading.end_chapter > book.chapter_count:
        raise HTTPException(
            status_code=422,
            detail=f"{book.name} only has {book.chapter_count} chapters "
                   f"(end_chapter: {reading.end_chapter})",
        )

    db_reading = Reading(
        book_id=reading.book_id,
        start_chapter=reading.start_chapter,
        start_verse=reading.start_verse,
        end_chapter=reading.end_chapter,
        end_verse=reading.end_verse,
        date_read=reading.date_read,
    )
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading


@router.get("/", response_model=list[ReadingRead])
def list_readings(
    canon: str = Query(default="P"),
    book_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Reading).join(Book).filter(Book.canon == canon)

    if book_id is not None:
        query = query.filter(Reading.book_id == book_id)
    if start_date is not None:
        query = query.filter(Reading.date_read >= start_date)
    if end_date is not None:
        query = query.filter(Reading.date_read <= end_date)

    return query.order_by(Reading.date_read.desc()).all()


@router.delete("/{reading_id}", status_code=204)
def delete_reading(reading_id: int, db: Session = Depends(get_db)):
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")

    db.delete(reading)
    db.commit()