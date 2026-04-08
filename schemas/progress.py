from pydantic import BaseModel

class BookProgress(BaseModel):
    book_id: int
    name: str
    chapter_count: int
    chapters_read: int
    percentage: float

class TestamentSummary(BaseModel):
    chapter_count: int
    chapters_read: int
    chapter_percentage: float
    verse_count: int

class HeatmapDay(BaseModel):
    date: str
    count: int