from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()


# Request model
class Note(BaseModel):
    id: int
    title: str
    content: str


# Response model
class NoteOut(BaseModel):
    id: int
    title: str


# In-memory database
fake_notes_db = []


# CREATE NOTE
@app.post(
    "/notes/",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED
)
def add_note(note: Note):

    # Check duplicate ID
    for existing_note in fake_notes_db:
        if existing_note.id == note.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Note ID already exists"
            )

    fake_notes_db.append(note)

    return note


# LIST NOTES
@app.get(
    "/notes/",
    response_model=List[NoteOut],
    status_code=status.HTTP_200_OK
)
def get_notes(title: Optional[str] = None):

    if title:
        return [
            note
            for note in fake_notes_db
            if note.title.lower() == title.lower()
        ]

    return fake_notes_db


# UPDATE NOTE
@app.put(
    "/notes/{note_id}",
    response_model=NoteOut,
    status_code=status.HTTP_200_OK
)
def update_note(note_id: int, updated_note: Note):

    for index, note in enumerate(fake_notes_db):

        if note.id == note_id:

            # Make sure the URL ID and body ID match
            if updated_note.id != note_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Note ID in URL and request body must match"
                )

            fake_notes_db[index] = updated_note

            return updated_note

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Note not found"
    )


# DELETE NOTE
@app.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_note(note_id: int):

    for index, note in enumerate(fake_notes_db):

        if note.id == note_id:

            fake_notes_db.pop(index)

            # 204 response should not return a response body
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Note not found"
    )