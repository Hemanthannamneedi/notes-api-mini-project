from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List

app = FastAPI()


# =========================
# User Models
# =========================

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=20)
    age: int = Field(..., ge=18, le=100)
    country: Optional[str] = None

    @validator("username")
    def validate_username(cls, value):
        if not value.replace("_", "").isalnum():
            raise ValueError(
                "Username can contain only letters, numbers and underscores"
            )
        return value

    @validator("password")
    def validate_password(cls, value):
        if not any(char.isupper() for char in value):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )

        if not any(char.isdigit() for char in value):
            raise ValueError(
                "Password must contain at least one number"
            )

        return value


class UserOut(BaseModel):
    username: str
    email: EmailStr
    age: int
    country: Optional[str] = None


# =========================
# Note Models
# =========================

class Note(BaseModel):
    id: int
    title: str = Field(..., min_length=3, max_length=50)
    content: str = Field(..., min_length=5, max_length=500)


class NoteOut(BaseModel):
    id: int
    title: str
    content: str


# In-memory database
fake_notes_db = []


# =========================
# User API
# =========================

@app.post("/users/")
def create_user(user: User):
    return {
        "message": "User created successfully",
        "user": UserOut(
            username=user.username,
            email=user.email,
            age=user.age,
            country=user.country
        )
    }


# =========================
# Notes API
# =========================

@app.post("/notes/", response_model=NoteOut, status_code=201)
def add_note(note: Note):

    for existing_note in fake_notes_db:
        if existing_note.id == note.id:
            raise HTTPException(
                status_code=400,
                detail="Note ID already exists"
            )

    fake_notes_db.append(note)

    return note


@app.get("/notes/", response_model=List[NoteOut])
def get_notes(title: Optional[str] = None):

    if title:
        return [
            note
            for note in fake_notes_db
            if note.title.lower() == title.lower()
        ]

    return fake_notes_db


@app.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, updated_note: Note):

    for index, note in enumerate(fake_notes_db):

        if note.id == note_id:

            if updated_note.id != note_id:
                raise HTTPException(
                    status_code=400,
                    detail="Note ID in URL and request body must match"
                )

            fake_notes_db[index] = updated_note

            return updated_note

    raise HTTPException(
        status_code=404,
        detail="Note not found"
    )


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int):

    for index, note in enumerate(fake_notes_db):

        if note.id == note_id:
            fake_notes_db.pop(index)
            return

    raise HTTPException(
        status_code=404,
        detail="Note not found"
    )


# =========================
# Body() Example
# =========================

@app.post("/message/")
def create_message(
    user: User,
    message: str = Body(...)
):
    return {
        "username": user.username,
        "message": message
    }