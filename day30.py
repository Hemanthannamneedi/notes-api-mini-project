from fastapi import FastAPI, HTTPException, UploadFile, File, status
from pydantic import BaseModel, Field
from typing import Optional, List
import os

app = FastAPI(
    title="Enhanced Notes API",
    description="Notes API with validation, error handling, response models and file uploads",
    version="1.0.0"
)


# =========================
# File Upload Configuration
# =========================

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# =========================
# Request Model
# =========================

class NoteIn(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=50
    )

    content: str = Field(
        ...,
        min_length=5,
        max_length=500
    )


# =========================
# Response Model
# =========================

class NoteOut(BaseModel):
    id: int
    title: str
    content: str
    attached_file: Optional[str] = None


# =========================
# In-Memory Database
# =========================

fake_notes_db = []


# =========================
# Helper Function
# =========================

def find_note(note_id: int):

    for note in fake_notes_db:
        if note["id"] == note_id:
            return note

    return None


# =========================
# Home
# =========================

@app.get("/")
def home():

    return {
        "message": "Enhanced Notes API is running"
    }


# =========================
# CREATE NOTE
# =========================

@app.post(
    "/notes/",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED
)
def create_note(note: NoteIn):

    # Generate new ID
    if fake_notes_db:
        new_id = max(
            existing_note["id"]
            for existing_note in fake_notes_db
        ) + 1
    else:
        new_id = 1

    new_note = {
        "id": new_id,
        "title": note.title,
        "content": note.content,
        "attached_file": None
    }

    fake_notes_db.append(new_note)

    return new_note


# =========================
# GET ALL NOTES
# =========================

@app.get(
    "/notes/",
    response_model=List[NoteOut],
    status_code=status.HTTP_200_OK
)
def get_notes():

    return fake_notes_db


# =========================
# GET SINGLE NOTE
# =========================

@app.get(
    "/notes/{note_id}",
    response_model=NoteOut,
    status_code=status.HTTP_200_OK
)
def get_note(note_id: int):

    note = find_note(note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    return note


# =========================
# UPDATE NOTE
# =========================

@app.put(
    "/notes/{note_id}",
    response_model=NoteOut,
    status_code=status.HTTP_200_OK
)
def update_note(
    note_id: int,
    updated_note: NoteIn
):

    note = find_note(note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    note["title"] = updated_note.title
    note["content"] = updated_note.content

    return note


# =========================
# DELETE NOTE
# =========================

@app.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_note(note_id: int):

    note = find_note(note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    fake_notes_db.remove(note)

    return


# =========================
# FILE ATTACHMENT
# =========================

@app.post(
    "/notes/{note_id}/attachment",
    response_model=NoteOut,
    status_code=status.HTTP_200_OK
)
async def attach_file(
    note_id: int,
    assignment_file: UploadFile = File(...)
):

    note = find_note(note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    # Create filename
    filename = f"{note_id}_{assignment_file.filename}"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    # Save file
    try:

        with open(file_path, "wb") as file:

            while True:

                chunk = await assignment_file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                file.write(chunk)

    finally:
        await assignment_file.close()

    # Store filename in note
    note["attached_file"] = assignment_file.filename

    return note