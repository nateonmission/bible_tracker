import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.book import Book
from models.reading import Reading
from main import app

# ---------------------------------------------------------------------------
# Test database setup
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///test_bible_tracker.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


from routes.readings import get_db as _r_get_db
from routes.progress import get_db as _p_get_db

app.dependency_overrides[_r_get_db] = override_get_db
app.dependency_overrides[_p_get_db] = override_get_db

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Create tables and seed test books before each test, drop after."""
    Base.metadata.create_all(bind=engine)

    db = TestSession()
    # Seed a few books for testing
    if db.query(Book).count() == 0:
        test_books = [
            Book(id=1, name="Genesis", canon="P", testament="OT", chapter_count=50, verse_count=1533, book_order=1),
            Book(id=2, name="Exodus", canon="P", testament="OT", chapter_count=40, verse_count=1213, book_order=2),
            Book(id=3, name="Matthew", canon="P", testament="NT", chapter_count=28, verse_count=1071, book_order=40),
            Book(id=4, name="Revelation", canon="P", testament="NT", chapter_count=22, verse_count=404, book_order=66),
            Book(id=5, name="Tobit", canon="P", testament="AP", chapter_count=14, verse_count=245, book_order=67),
        ]
        db.add_all(test_books)
        db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# POST /api/readings
# ---------------------------------------------------------------------------

class TestCreateReading:
    def test_create_reading_success(self):
        response = client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 1,
            "start_verse": 1,
            "end_chapter": 3,
            "end_verse": 24,
            "date_read": "2026-04-01",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["book_id"] == 1
        assert data["start_chapter"] == 1
        assert data["end_chapter"] == 3
        assert data["start_verse"] == 1
        assert data["end_verse"] == 24
        assert data["date_read"] == "2026-04-01"
        assert "id" in data
        assert "created_at" in data

    def test_create_reading_defaults_to_today(self):
        response = client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 1,
            "start_verse": 1,
            "end_chapter": 1,
            "end_verse": 31,
        })
        assert response.status_code == 201
        assert response.json()["date_read"] == date.today().isoformat()

    def test_create_reading_single_verse(self):
        response = client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 1,
            "start_verse": 1,
            "end_chapter": 1,
            "end_verse": 1,
            "date_read": "2026-04-01",
        })
        assert response.status_code == 201

    def test_reject_invalid_start_chapter(self):
        response = client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 51,
            "start_verse": 1,
            "end_chapter": 51,
            "end_verse": 1,
            "date_read": "2026-04-01",
        })
        assert response.status_code == 422
        assert "50 chapters" in response.json()["detail"]

    def test_reject_invalid_end_chapter(self):
        response = client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 1,
            "start_verse": 1,
            "end_chapter": 51,
            "end_verse": 1,
            "date_read": "2026-04-01",
        })
        assert response.status_code == 422
        assert "50 chapters" in response.json()["detail"]

    def test_reject_end_chapter_before_start(self):
        response = client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 5,
            "start_verse": 1,
            "end_chapter": 3,
            "end_verse": 1,
            "date_read": "2026-04-01",
        })
        assert response.status_code == 422

    def test_reject_end_verse_before_start_same_chapter(self):
        response = client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 1,
            "start_verse": 10,
            "end_chapter": 1,
            "end_verse": 5,
            "date_read": "2026-04-01",
        })
        assert response.status_code == 422

    def test_reject_zero_chapter(self):
        response = client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 0,
            "start_verse": 1,
            "end_chapter": 1,
            "end_verse": 1,
            "date_read": "2026-04-01",
        })
        assert response.status_code == 422

    def test_reject_negative_verse(self):
        response = client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 1,
            "start_verse": -1,
            "end_chapter": 1,
            "end_verse": 1,
            "date_read": "2026-04-01",
        })
        assert response.status_code == 422

    def test_reject_nonexistent_book(self):
        response = client.post("/api/readings/", json={
            "book_id": 9999,
            "start_chapter": 1,
            "start_verse": 1,
            "end_chapter": 1,
            "end_verse": 1,
            "date_read": "2026-04-01",
        })
        assert response.status_code == 404

    def test_reject_book_wrong_canon(self):
        """Tobit (AP book) should not be found when canon=P is default but book has canon=P in test data."""
        # This tests that canon filtering works — adjust if your test seed uses different canons
        response = client.post("/api/readings/?canon=J", json={
            "book_id": 1,
            "start_chapter": 1,
            "start_verse": 1,
            "end_chapter": 1,
            "end_verse": 1,
            "date_read": "2026-04-01",
        })
        assert response.status_code == 404

    def test_duplicate_readings_allowed(self):
        """Same book, chapter, and date should be allowed (user re-read it)."""
        payload = {
            "book_id": 1,
            "start_chapter": 1,
            "start_verse": 1,
            "end_chapter": 1,
            "end_verse": 31,
            "date_read": "2026-04-01",
        }
        r1 = client.post("/api/readings/", json=payload)
        r2 = client.post("/api/readings/", json=payload)
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["id"] != r2.json()["id"]


# ---------------------------------------------------------------------------
# GET /api/readings
# ---------------------------------------------------------------------------

class TestListReadings:
    def _seed_readings(self):
        """Helper to create a few readings."""
        readings = [
            {"book_id": 1, "start_chapter": 1, "start_verse": 1, "end_chapter": 1, "end_verse": 31, "date_read": "2026-04-01"},
            {"book_id": 1, "start_chapter": 2, "start_verse": 1, "end_chapter": 2, "end_verse": 25, "date_read": "2026-04-02"},
            {"book_id": 3, "start_chapter": 1, "start_verse": 1, "end_chapter": 1, "end_verse": 25, "date_read": "2026-04-03"},
        ]
        for r in readings:
            client.post("/api/readings/", json=r)

    def test_list_all_readings(self):
        self._seed_readings()
        response = client.get("/api/readings/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_ordered_by_date_descending(self):
        self._seed_readings()
        response = client.get("/api/readings/")
        data = response.json()
        dates = [r["date_read"] for r in data]
        assert dates == sorted(dates, reverse=True)

    def test_filter_by_book_id(self):
        self._seed_readings()
        response = client.get("/api/readings/?book_id=1")
        data = response.json()
        assert len(data) == 2
        assert all(r["book_id"] == 1 for r in data)

    def test_filter_by_date_range(self):
        self._seed_readings()
        response = client.get("/api/readings/?start_date=2026-04-02&end_date=2026-04-03")
        data = response.json()
        assert len(data) == 2

    def test_filter_by_start_date_only(self):
        self._seed_readings()
        response = client.get("/api/readings/?start_date=2026-04-03")
        data = response.json()
        assert len(data) == 1
        assert data[0]["date_read"] == "2026-04-03"

    def test_empty_results(self):
        response = client.get("/api/readings/?book_id=9999")
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# DELETE /api/readings/{id}
# ---------------------------------------------------------------------------

class TestDeleteReading:
    def test_delete_reading(self):
        r = client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 1,
            "start_verse": 1,
            "end_chapter": 1,
            "end_verse": 31,
            "date_read": "2026-04-01",
        })
        reading_id = r.json()["id"]

        delete_response = client.delete(f"/api/readings/{reading_id}")
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = client.get("/api/readings/")
        ids = [r["id"] for r in get_response.json()]
        assert reading_id not in ids

    def test_delete_nonexistent_reading(self):
        response = client.delete("/api/readings/9999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/progress
# ---------------------------------------------------------------------------

class TestProgress:
    def test_progress_empty(self):
        response = client.get("/api/progress?canon=P")
        assert response.status_code == 200
        data = response.json()
        # All books should show 0 chapters read
        for testament in data.values():
            for book in testament:
                assert book["chapters_read"] == 0
                assert book["percentage"] == 0

    def test_progress_after_readings(self):
        # Read Genesis chapters 1-3
        client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 1,
            "start_verse": 1,
            "end_chapter": 3,
            "end_verse": 22,
            "date_read": "2026-04-01",
        })

        response = client.get("/api/progress?canon=P")
        data = response.json()
        genesis = next(b for b in data["OT"] if b["name"] == "Genesis")
        assert genesis["chapters_read"] == 3
        assert genesis["percentage"] == round((3 / 50) * 100, 1)

    def test_progress_overlapping_ranges(self):
        """Overlapping readings should not double-count chapters."""
        client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 1, "start_verse": 1,
            "end_chapter": 5, "end_verse": 32,
            "date_read": "2026-04-01",
        })
        client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 3, "start_verse": 1,
            "end_chapter": 7, "end_verse": 24,
            "date_read": "2026-04-02",
        })

        response = client.get("/api/progress?canon=P")
        data = response.json()
        genesis = next(b for b in data["OT"] if b["name"] == "Genesis")
        # Chapters 1-7 = 7 unique chapters
        assert genesis["chapters_read"] == 7

    def test_progress_grouped_by_testament(self):
        response = client.get("/api/progress?canon=P")
        data = response.json()
        assert "OT" in data
        assert "NT" in data


# ---------------------------------------------------------------------------
# GET /api/progress/summary
# ---------------------------------------------------------------------------

class TestProgressSummary:
    def test_summary_empty(self):
        response = client.get("/api/progress/summary?canon=P")
        assert response.status_code == 200
        data = response.json()
        assert data["total"]["chapters_read"] == 0
        assert data["total"]["chapter_percentage"] == 0

    def test_summary_after_readings(self):
        # Read Genesis 1-10 and Matthew 1-5
        client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 1, "start_verse": 1,
            "end_chapter": 10, "end_verse": 32,
            "date_read": "2026-04-01",
        })
        client.post("/api/readings/", json={
            "book_id": 3,
            "start_chapter": 1, "start_verse": 1,
            "end_chapter": 5, "end_verse": 48,
            "date_read": "2026-04-01",
        })

        response = client.get("/api/progress/summary?canon=P")
        data = response.json()

        assert data["OT"]["chapters_read"] == 10
        assert data["NT"]["chapters_read"] == 5
        assert data["total"]["chapters_read"] == 15

    def test_summary_has_verse_counts(self):
        response = client.get("/api/progress/summary?canon=P")
        data = response.json()
        assert data["OT"]["verse_count"] > 0
        assert data["NT"]["verse_count"] > 0
        assert data["total"]["verse_count"] > 0


# ---------------------------------------------------------------------------
# GET /api/heatmap
# ---------------------------------------------------------------------------

class TestHeatmap:
    def test_heatmap_returns_365_entries(self):
        response = client.get("/api/heatmap")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 365

    def test_heatmap_date_range(self):
        response = client.get("/api/heatmap")
        data = response.json()
        today = date.today()
        start = today - timedelta(days=364)
        assert data[0]["date"] == start.isoformat()
        assert data[-1]["date"] == today.isoformat()

    def test_heatmap_all_zero_when_empty(self):
        response = client.get("/api/heatmap")
        data = response.json()
        assert all(d["count"] == 0 for d in data)

    def test_heatmap_counts_readings(self):
        today = date.today().isoformat()
        client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 1, "start_verse": 1,
            "end_chapter": 1, "end_verse": 31,
            "date_read": today,
        })
        client.post("/api/readings/", json={
            "book_id": 1,
            "start_chapter": 2, "start_verse": 1,
            "end_chapter": 2, "end_verse": 25,
            "date_read": today,
        })

        response = client.get("/api/heatmap")
        data = response.json()
        today_entry = next(d for d in data if d["date"] == today)
        # Genesis 1:1-31 = 31 verses, Genesis 2:1-25 = 25 verses
        assert today_entry["count"] == 56

    def test_heatmap_consecutive_dates(self):
        """Verify no gaps in date sequence."""
        response = client.get("/api/heatmap")
        data = response.json()
        for i in range(1, len(data)):
            prev = date.fromisoformat(data[i - 1]["date"])
            curr = date.fromisoformat(data[i]["date"])
            assert (curr - prev).days == 1, f"Gap between {prev} and {curr}"