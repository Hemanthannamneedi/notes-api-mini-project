from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os

app = FastAPI()


# =========================
# File Upload Configuration
# =========================

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# =========================
# Note Models
# =========================

class Note(BaseModel):
    id: int
    title: str
    content: str


class NoteOut(BaseModel):
    id: int
    title: str
    content: str
    attachment: Optional[str] = None


# In-memory database
fake_notes_db = []


# =========================
# Simple File Upload API
# =========================

@app.post("/upload/")
async def upload_file(
    assignment_file: UploadFile = File(...)
):
    file_path = os.path.join(
        UPLOAD_FOLDER,
        assignment_file.filename
    )

    try:
        with open(file_path, "wb") as file:
            while True:
                chunk = await assignment_file.read(1024 * 1024)

                if not chunk:
                    break

                file.write(chunk)

    finally:
        await assignment_file.close()

    return {
        "message": "File uploaded successfully",
        "filename": assignment_file.filename,
        "content_type": assignment_file.content_type,
        "file_path": file_path
    }


# =========================
# Notes API
# =========================

@app.post("/notes/", response_model=NoteOut)
def add_note(note: Note):

    for existing_note in fake_notes_db:
        if existing_note["id"] == note.id:
            raise HTTPException(
                status_code=400,
                detail="Note ID already exists"
            )

    note_data = {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "attachment": None
    }

    fake_notes_db.append(note_data)

    return note_data


@app.get("/notes/", response_model=List[NoteOut])
def get_notes():

    return fake_notes_db


# =========================
# Add File Attachment
# =========================

@app.post("/notes/{note_id}/attachment/")
async def upload_note_attachment(
    note_id: int,
    assignment_file: UploadFile = File(...)
):

    # Find note
    selected_note = None

    for note in fake_notes_db:
        if note["id"] == note_id:
            selected_note = note
            break

    if selected_note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    # Create unique filename
    filename = f"{note_id}_{assignment_file.filename}"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    try:
        with open(file_path, "wb") as file:

            while True:
                chunk = await assignment_file.read(1024 * 1024)

                if not chunk:
                    break

                file.write(chunk)

    finally:
        await assignment_file.close()

    # Save attachment information
    selected_note["attachment"] = file_path

    return {
        "message": "File attached to note successfully",
        "note_id": note_id,
        "filename": assignment_file.filename,
        "content_type": assignment_file.content_type,
        "file_path": file_path
    }


# =========================
# Upload File + Note Data
# =========================

@app.post("/notes-with-file/")
async def create_note_with_file(
    id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    assignment_file: UploadFile = File(...)
):

    # Check duplicate ID
    for note in fake_notes_db:
        if note["id"] == id:
            raise HTTPException(
                status_code=400,
                detail="Note ID already exists"
            )

    filename = f"{id}_{assignment_file.filename}"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    try:
        with open(file_path, "wb") as file:

            while True:
                chunk = await assignment_file.read(1024 * 1024)

                if not chunk:
                    break

                file.write(chunk)

    finally:
        await assignment_file.close()

    note = {
        "id": id,
        "title": title,
        "content": content,
        "attachment": file_path
    }

    fake_notes_db.append(note)

    return {
        "message": "Note created with attachment",
        "note": note,
        "filename": assignment_file.filename,
        "content_type": assignment_file.content_type
    }