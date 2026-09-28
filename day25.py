from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


class Note(BaseModel):
    id: int
    title: str
    content: str


fake_notes_db = []


@app.post("/notes/")
def add_note(note: Note):
    for existing_note in fake_notes_db:
        if existing_note.id == note.id:
            raise HTTPException(
                status_code=400,
                detail="Note ID already exists"
            )

    fake_notes_db.append(note)
    return {
        "message": "Note added successfully",
        "note": note
    }


@app.get("/notes/")
def get_notes(title: Optional[str] = None):

    if title:
        return [
            note for note in fake_notes_db
            if note.title.lower() == title.lower()
        ]

    return fake_notes_db


@app.put("/notes/{note_id}")
def update_note(note_id: int, updated_note: Note):

    for index, note in enumerate(fake_notes_db):
        if note.id == note_id:
            fake_notes_db[index] = updated_note

            return {
                "message": "Note updated successfully",
                "note": updated_note
            }

    raise HTTPException(
        status_code=404,
        detail="Note not found"
    )


@app.delete("/notes/{note_id}")
def delete_note(note_id: int):

    for index, note in enumerate(fake_notes_db):
        if note.id == note_id:
            deleted_note = fake_notes_db.pop(index)

            return {
                "message": "Note deleted successfully",
                "note": deleted_note
            }

    raise HTTPException(
        status_code=404,
        detail="Note not found"
    )