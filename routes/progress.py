from datetime import date, timedelta

from typing import Optional

from fastapi import APIRouter, Depends, Query
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


# Books with the same text but different names across canons.
# Maps every non-canonical name → the Protestant/canonical name used as the key.
BOOK_NAME_ALIASES: dict[str, str] = {
    # Catholic variants
    "Song of Songs":                     "Song of Solomon",
    "Daniel (with additions)":           "Daniel",
    "Esther (with additions)":           "Esther",
    "Baruch (with Letter of Jeremiah)":  "Baruch",
    # Jewish transliterated names → Protestant name
    "Genesis (Bereshit)":        "Genesis",
    "Exodus (Shemot)":           "Exodus",
    "Leviticus (Vayikra)":       "Leviticus",
    "Numbers (Bamidbar)":        "Numbers",
    "Deuteronomy (Devarim)":     "Deuteronomy",
    "Joshua (Yehoshua)":         "Joshua",
    "Judges (Shoftim)":          "Judges",
    "Isaiah (Yeshayahu)":        "Isaiah",
    "Jeremiah (Yirmiyahu)":      "Jeremiah",
    "Ezekiel (Yechezkel)":       "Ezekiel",
    "Psalms (Tehillim)":         "Psalms",
    "Proverbs (Mishlei)":        "Proverbs",
    "Job (Iyov)":                "Job",
    "Song of Songs (Shir HaShirim)": "Song of Solomon",
    "Ruth (Rut)":                "Ruth",
    "Lamentations (Eikhah)":     "Lamentations",
    "Ecclesiastes (Qohelet)":    "Ecclesiastes",
    "Esther (Esther)":           "Esther",
    "Daniel (Daniel)":           "Daniel",
}

# Jewish combined books: maps the combined name to a list of
# (constituent Protestant name, chapter offset in the combined book).
# e.g. 2 Samuel ch 1 becomes Samuel ch 32 (offset = 31 chapters of 1 Samuel).
COMBINED_BOOKS: dict[str, list[tuple[str, int]]] = {
    "Samuel (1-2 Samuel)": [
        ("1 Samuel", 0),
        ("2 Samuel", 31),
    ],
    "Kings (1-2 Kings)": [
        ("1 Kings", 0),
        ("2 Kings", 22),
    ],
    "Chronicles (1-2 Chronicles)": [
        ("1 Chronicles", 0),
        ("2 Chronicles", 29),
    ],
    "Ezra-Nehemiah": [
        ("Ezra",     0),
        ("Nehemiah", 10),
    ],
    # The Twelve Minor Prophets in canonical order
    "The Twelve (Trei Asar)": [
        ("Hosea",     0),
        ("Joel",      14),
        ("Amos",      17),
        ("Obadiah",   26),
        ("Jonah",     27),
        ("Micah",     31),
        ("Nahum",     38),
        ("Habakkuk",  41),
        ("Zephaniah", 44),
        ("Haggai",    47),
        ("Zechariah", 49),
        ("Malachi",   63),
    ],
}


def _book_ids_for_name(db: Session, name: str) -> list[int]:
    """Return all book IDs matching a canonical name or any of its aliases."""
    canonical = BOOK_NAME_ALIASES.get(name, name)
    all_names = {canonical} | {
        alias for alias, target in BOOK_NAME_ALIASES.items() if target == canonical
    }
    return [b.id for b in db.query(Book.id).filter(Book.name.in_(all_names)).all()]


def get_chapters_read(db: Session, book_name: str) -> int:
    """Count distinct chapters read for a book across all canons."""
    if book_name in COMBINED_BOOKS:
        chapters: set[int] = set()
        for constituent, offset in COMBINED_BOOKS[book_name]:
            book_ids = _book_ids_for_name(db, constituent)
            readings = (
                db.query(Reading.start_chapter, Reading.end_chapter)
                .filter(Reading.book_id.in_(book_ids))
                .all()
            )
            for start, end in readings:
                chapters.update(range(start + offset, end + offset + 1))
        return len(chapters)

    book_ids = _book_ids_for_name(db, book_name)
    readings = (
        db.query(Reading.start_chapter, Reading.end_chapter)
        .filter(Reading.book_id.in_(book_ids))
        .all()
    )
    chapters: set[int] = set()
    for start, end in readings:
        chapters.update(range(start, end + 1))
    return len(chapters)


@router.get("/progress")
def get_progress(canon: str = Query(default="P"), db: Session = Depends(get_db)):
    books = db.query(Book).filter(Book.canon == canon).order_by(Book.book_order).all()

    result = {"OT": [], "NT": [], "AP": []}

    for book in books:
        chapters_read = get_chapters_read(db, book.name)
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

        chapters_read = sum(get_chapters_read(db, b.name) for b in books)

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