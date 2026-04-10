from database import engine, SessionLocal
from models.book import Book
from sqlalchemy import inspect
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_db():
    # Check tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables found: {tables}")
    assert "books" in tables, "ERROR: 'books' table missing"

    db = SessionLocal()
    try:
        total = db.query(Book).count()
        print(f"\nTotal books: {total}")

        # Check per-canon counts
        for canon in ("P", "C", "J"):
            count = db.query(Book).filter(Book.canon == canon).count()
            print(f"  Canon '{canon}': {count} books")

        # Check per-testament counts
        for testament in ("OT", "NT", "AP"):
            count = db.query(Book).filter(Book.testament == testament).count()
            if count > 0:
                print(f"  Testament '{testament}': {count} books")

        # Spot check a few books
        genesis = db.query(Book).filter(Book.name == "Genesis", Book.canon == "P").first()
        assert genesis is not None, "ERROR: Genesis not found in Protestant canon"
        assert genesis.chapter_count == 50, f"ERROR: Genesis should have 50 chapters, got {genesis.chapter_count}"
        assert genesis.testament == "OT", f"ERROR: Genesis should be OT, got {genesis.testament}"
        print(f"\nSpot check — Genesis (P): {genesis.chapter_count} chapters, {genesis.verse_count} verses ✓")

        rev = db.query(Book).filter(Book.name == "Revelation", Book.canon == "P").first()
        assert rev is not None, "ERROR: Revelation not found in Protestant canon"
        assert rev.chapter_count == 22, f"ERROR: Revelation should have 22 chapters, got {rev.chapter_count}"
        print(f"Spot check — Revelation (P): {rev.chapter_count} chapters, {rev.verse_count} verses ✓")

        # Check book_order is sequential per canon
        for canon in ("P", "C", "J"):
            books = db.query(Book).filter(Book.canon == canon).order_by(Book.book_order).all()
            orders = [b.book_order for b in books]
            expected = list(range(1, len(books) + 1))
            assert orders == expected, f"ERROR: Canon '{canon}' book_order not sequential: {orders}"
            print(f"Book order sequential for canon '{canon}' ✓")

        print("\n✅ All checks passed.")

    finally:
        db.close()


if __name__ == "__main__":
    try:
        test_db()
    except Exception as e:
        print(f"ERROR: {e}")