from pydantic import BaseModel, Field
from typing import Optional


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    content: str = Field(..., min_length=5, max_length=2000)
    user_id: int


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    content: Optional[str] = Field(None, min_length=5, max_length=2000)


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    user_id: int
    attached_file: Optional[str] = None

    class Config:
        orm_mode = True