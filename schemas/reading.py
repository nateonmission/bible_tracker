# schemas/reading.py


from pydantic import BaseModel, field_validator, Field
from datetime import date, datetime


class ReadingBase(BaseModel):
    book_id: int

    start_chapter: int
    start_verse: int

    end_chapter: int
    end_verse: int

    date_read: date

    @field_validator("start_chapter", "start_verse", "end_chapter", "end_verse")
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("must be greater than 0")
        return v

    @field_validator("end_chapter")
    def validate_range(cls, end_chapter, values):
        start_chapter = values.data.get("start_chapter")
        if start_chapter and end_chapter < start_chapter:
            raise ValueError("end_chapter must be >= start_chapter")
        return end_chapter

    @field_validator("end_verse")
    def validate_verse_range(cls, end_verse, values):
        start_chapter = values.data.get("start_chapter")
        end_chapter = values.data.get("end_chapter")
        start_verse = values.data.get("start_verse")

        # Only enforce verse ordering if same chapter
        if start_chapter == end_chapter and start_verse:
            if end_verse < start_verse:
                raise ValueError("end_verse must be >= start_verse if same chapter")
        return end_verse
    
class ReadingCreate(ReadingBase):
    date_read: date = Field(default_factory=date.today)
    pass


class ReadingRead(ReadingBase):
    id: int
    created_at: datetime  
    model_config = {"from_attributes": True}