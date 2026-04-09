# seed_database.py

import csv
from pathlib import Path
from database import engine, SessionLocal, Base
from models.book import Book
from models.reading import Reading  # noqa: F401 — ensures table is registered with Base

CANON_FILES = {
    "P": "data/BIBLE_DATA_P.csv",
    "C": "data/BIBLE_DATA_C.csv",
    "J": "data/BIBLE_DATA_J.csv",
}

# Jewish CSV uses hyphens in column names
COLUMN_MAP = {
    "chapter-count": "chapter_count",
    "verse-count": "verse_count",
    "book-order": "book_order",
}


def normalize_row(row: dict) -> dict:
    """Normalize column names (handle hyphens vs underscores)."""
    return {COLUMN_MAP.get(k, k): v for k, v in row.items()}


def seed_books(db, canon: str, filepath: str):
    """Seed books for a single canon from a CSV file."""
    path = Path(filepath)
    if not path.exists():
        print(f"  WARNING: {filepath} not found, skipping.")
        return 0

    count = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = normalize_row(row)
            book = Book(
                name=row["name"].strip(),
                canon=canon,
                testament=row["testament"].strip(),
                chapter_count=int(row["chapter_count"]),
                verse_count=int(row["verse_count"]),
                book_order=int(row["book_order"]),
            )
            db.add(book)
            count += 1

    db.commit()
    print(f"  Seeded {count} books for canon '{canon}'.")
    return count


def init_db():
    """Create all tables and seed book data."""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.\n")

    db = SessionLocal()
    try:
        existing = db.query(Book).count()
        if existing > 0:
            print(f"Database already has {existing} books. Skipping seed.")
            print("To re-seed, delete bible_tracker.db and run again.")
            return

        print("Seeding book data...")
        total = 0
        for canon, filepath in CANON_FILES.items():
            total += seed_books(db, canon, filepath)

        print(f"\nDone. {total} total books seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()