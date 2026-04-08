# schemas/book.py

from pydantic import BaseModel, field_validator

class BookBase(BaseModel):
    name: str
    testament: str
    chapter_count: int
    verse_count: int
    book_order: int

    @field_validator("testament")
    def validate_testament(cls, v):
        if v not in {"OT", "NT", "AP"}:
            raise ValueError("testament must be OT, NT, or AP")
        return v
    
class BookRead(BookBase):
    id: int

    class Config:
        from_attributes = True