import os
import uuid
from typing import List

from fastapi import (
    FastAPI, Depends, HTTPException,
    UploadFile, File, status
)
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import User, Note
from schemas import NoteCreate, NoteUpdate, NoteResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enhanced Notes API",
    description="Database-backed Notes API using FastAPI and SQLAlchemy",
    version="2.0.0"
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Database-backed Notes API is running"}


# CREATE NOTE
@app.post(
    "/notes/",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED
)
def create_note(
    note_in: NoteCreate,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == note_in.user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    note = Note(
        title=note_in.title,
        content=note_in.content,
        user_id=note_in.user_id
    )

    try:
        db.add(note)
        db.commit()
        db.refresh(note)
        return note
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create note"
        )


# GET ALL NOTES
@app.get("/notes/", response_model=List[NoteResponse])
def get_notes(db: Session = Depends(get_db)):
    return db.query(Note).order_by(Note.id).all()


# GET NOTES BY ID
@app.get("/notes/{note_id}", response_model=NoteResponse)
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


# GET ALL NOTES FOR A USER
@app.get(
    "/users/{user_id}/notes/",
    response_model=List[NoteResponse]
)
def get_user_notes(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return db.query(Note).filter(
        Note.user_id == user_id
    ).order_by(Note.id).all()


# UPDATE NOTE
@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    note_in: NoteUpdate,
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

    changes = note_in.dict(exclude_unset=True)

    for field, value in changes.items():
        setattr(note, field, value)

    try:
        db.commit()
        db.refresh(note)
        return note
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update note"
        )


# DELETE NOTE
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

    try:
        db.delete(note)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete note"
        )

    return None


# ATTACH FILE TO A NOTE
@app.post("/notes/{note_id}/attachment/")
async def attach_file(
    note_id: int,
    assignment_file: UploadFile = File(...),
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

    # Keep the original extension, but generate a safe filename.
    extension = os.path.splitext(
        assignment_file.filename or ""
    )[1]

    safe_filename = "{}{}".format(uuid.uuid4().hex, extension)
    file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

    try:
        with open(file_path, "wb") as output_file:
            while True:
                chunk = await assignment_file.read(1024 * 1024)
                if not chunk:
                    break
                output_file.write(chunk)

        note.attached_file = safe_filename
        db.commit()
        db.refresh(note)

    except Exception:
        db.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail="Failed to attach file"
        )
    finally:
        await assignment_file.close()

    return {
        "message": "File attached successfully",
        "note_id": note_id,
        "filename": safe_filename
    }