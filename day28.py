from fastapi import (
    FastAPI,
    HTTPException,
    status,
    Form,
    Header
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

app = FastAPI()


# =========================
# Custom Exception
# =========================

class NegativeNumberException(Exception):
    def __init__(self, message: str):
        self.message = message


# =========================
# Custom Exception Handler
# =========================

@app.exception_handler(NegativeNumberException)
def negative_number_handler(request, exc):
    return JSONResponse(
        status_code=418,
        content={
            "error": "Negative Number",
            "message": exc.message
        }
    )


# =========================
# User Models
# =========================

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=20)
    age: int = Field(..., ge=18, le=100)
    country: Optional[str] = None


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
# Helper Function
# =========================

def note_not_found():
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Note not found",
        headers={
            "X-Error": "Note does not exist"
        }
    )


# =========================
# Home
# =========================

@app.get("/")
def home():
    return {
        "message": "Notes API is running"
    }


# =========================
# Create User
# =========================

@app.post(
    "/users/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED
)
def create_user(user: User):

    return user


# =========================
# Create Note
# =========================

@app.post(
    "/notes/",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED
)
def add_note(note: Note):

    for existing_note in fake_notes_db:

        if existing_note.id == note.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Note ID already exists"
            )

    fake_notes_db.append(note)

    return note


# =========================
# Get Notes
# =========================

@app.get(
    "/notes/",
    response_model=List[NoteOut],
    status_code=status.HTTP_200_OK
)
def get_notes(
    title: Optional[str] = None,
    limit: Optional[int] = None
):

    # Custom exception example
    if limit is not None and limit < 0:
        raise NegativeNumberException(
            "Limit cannot be a negative number"
        )

    if title:

        matching_notes = [
            note
            for note in fake_notes_db
            if note.title.lower() == title.lower()
        ]

        if not matching_notes:
            raise note_not_found()

        return matching_notes

    if limit is not None:
        return fake_notes_db[:limit]

    return fake_notes_db


# =========================
# Get Single Note
# =========================

@app.get(
    "/notes/{note_id}",
    response_model=NoteOut,
    status_code=status.HTTP_200_OK
)
def get_note(note_id: int):

    for note in fake_notes_db:

        if note.id == note_id:
            return note

    raise note_not_found()


# =========================
# Update Note
# =========================

@app.put(
    "/notes/{note_id}",
    response_model=NoteOut,
    status_code=status.HTTP_200_OK
)
def update_note(
    note_id: int,
    updated_note: Note
):

    for index, note in enumerate(fake_notes_db):

        if note.id == note_id:

            if updated_note.id != note_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Note ID in URL and request body must match"
                )

            fake_notes_db[index] = updated_note

            return updated_note

    raise note_not_found()


# =========================
# Delete Note
# =========================

@app.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_note(note_id: int):

    for index, note in enumerate(fake_notes_db):

        if note.id == note_id:

            fake_notes_db.pop(index)

            return

    raise note_not_found()


# =========================
# Form Data
# =========================

@app.post("/login/")
def login(
    username: str = Form(...),
    password: str = Form(...)
):

    if username == "" or password == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )

    return {
        "message": "Login data received",
        "username": username
    }


# =========================
# Custom Header
# =========================

@app.get("/header-info/")
def header_info(
    user_agent: Optional[str] = Header(None)
):

    if not user_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User-Agent header is required"
        )

    return {
        "user_agent": user_agent
    }
