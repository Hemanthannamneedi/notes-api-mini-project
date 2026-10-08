from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List

from database import engine, Base, get_db
from models import Note

app = FastAPI(
    title="FastAPI Notes CRUD"
)

Base.metadata.create_all(bind=engine)


# Pydantic request model
class NoteCreate(BaseModel):
    title: str
    content: str
    attachment_url: Optional[str] = None
    user_id: int


# Pydantic response model
class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    attachment_url: Optional[str] = None
    user_id: int

    class Config:
        orm_mode = True


# CREATE - POST
@app.post(
    "/notes/",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED
)
def create_note(
    note_in: NoteCreate,
    db: Session = Depends(get_db)
):
    new_note = Note(
        title=note_in.title,
        content=note_in.content,
        attachment_url=note_in.attachment_url,
        user_id=note_in.user_id
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return new_note


# READ - GET ALL
@app.get(
    "/notes/",
    response_model=List[NoteResponse]
)
def get_notes(
    db: Session = Depends(get_db)
):
    notes = db.query(Note).all()

    return notes


# READ - GET BY ID
@app.get(
    "/notes/{note_id}",
    response_model=NoteResponse
)
def get_note(
    note_id: int,
    db: Session = Depends(get_db)
):
    note = db.query(Note).filter(
        Note.id == note_id
    ).first()

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    return note


# UPDATE - PUT
@app.put(
    "/notes/{note_id}",
    response_model=NoteResponse
)
def update_note(
    note_id: int,
    note_in: NoteCreate,
    db: Session = Depends(get_db)
):
    note = db.query(Note).filter(
        Note.id == note_id
    ).first()

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    note.title = note_in.title
    note.content = note_in.content
    note.attachment_url = note_in.attachment_url
    note.user_id = note_in.user_id

    db.commit()
    db.refresh(note)

    return note


# DELETE
@app.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db)
):
    note = db.query(Note).filter(
        Note.id == note_id
    ).first()

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    db.delete(note)
    db.commit()

    return