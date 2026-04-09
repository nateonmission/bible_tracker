# routes/progress.py

from datetime import date, timedelta

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models.book import Book
from models.reading import Reading

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/books")
def get_books(
    canon: str = Query(default="P"),
    testament: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Book).filter(Book.canon == canon)
    if testament:
        query = query.filter(Book.testament == testament)
    books = query.order_by(Book.book_order).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "testament": b.testament,
            "chapter_count": b.chapter_count,
        }
        for b in books
    ]


def get_chapters_read(db: Session, book_id: int) -> int:
    """Count distinct chapters read by expanding start_chapter–end_chapter ranges."""
    readings = (
        db.query(Reading.start_chapter, Reading.end_chapter)
        .filter(Reading.book_id == book_id)
        .all()
    )

    chapters = set()
    for start, end in readings:
        chapters.update(range(start, end + 1))

    return len(chapters)


@router.get("/progress")
def get_progress(canon: str = Query(default="P"), db: Session = Depends(get_db)):
    books = db.query(Book).filter(Book.canon == canon).order_by(Book.book_order).all()

    result = {"OT": [], "NT": [], "AP": []}

    for book in books:
        chapters_read = get_chapters_read(db, book.id)
        percentage = round((chapters_read / book.chapter_count) * 100, 1) if book.chapter_count > 0 else 0

        book_data = {
            "book_id": book.id,
            "name": book.name,
            "chapter_count": book.chapter_count,
            "chapters_read": chapters_read,
            "percentage": percentage,
        }

        if book.testament in result:
            result[book.testament].append(book_data)

    return result


@router.get("/progress/summary")
def get_progress_summary(canon: str = Query(default="P"), db: Session = Depends(get_db)):
    summary = {}

    testaments = (
        db.query(Book.testament)
        .filter(Book.canon == canon)
        .distinct()
        .all()
    )

    total_chapters = 0
    total_chapters_read = 0
    total_verses = 0

    for (testament,) in testaments:
        books = db.query(Book).filter(Book.canon == canon, Book.testament == testament).all()

        chapter_count = sum(b.chapter_count for b in books)
        verse_count = sum(b.verse_count for b in books)

        chapters_read = sum(get_chapters_read(db, b.id) for b in books)

        chapter_pct = round((chapters_read / chapter_count) * 100, 1) if chapter_count > 0 else 0

        summary[testament] = {
            "chapter_count": chapter_count,
            "chapters_read": chapters_read,
            "chapter_percentage": chapter_pct,
            "verse_count": verse_count,
        }

        total_chapters += chapter_count
        total_chapters_read += chapters_read
        total_verses += verse_count

    summary["total"] = {
        "chapter_count": total_chapters,
        "chapters_read": total_chapters_read,
        "chapter_percentage": round((total_chapters_read / total_chapters) * 100, 1) if total_chapters > 0 else 0,
        "verse_count": total_verses,
    }

    return summary


@router.get("/heatmap")
def get_heatmap(db: Session = Depends(get_db)):
    today = date.today()
    start = today - timedelta(days=364)

    readings = (
        db.query(Reading, Book)
        .join(Book, Reading.book_id == Book.id)
        .filter(Reading.date_read >= start, Reading.date_read <= today)
        .all()
    )

    verse_map: dict[date, int] = {}
    for reading, book in readings:
        if reading.start_chapter == reading.end_chapter:
            verses = reading.end_verse - reading.start_verse + 1
        else:
            avg = book.verse_count / book.chapter_count if book.chapter_count else 0
            verses = round(avg * (reading.end_chapter - reading.start_chapter + 1))
        verse_map[reading.date_read] = verse_map.get(reading.date_read, 0) + verses

    heatmap = []
    for i in range(365):
        d = start + timedelta(days=i)
        heatmap.append({
            "date": d.isoformat(),
            "count": verse_map.get(d, 0),
        })

    return heatmap