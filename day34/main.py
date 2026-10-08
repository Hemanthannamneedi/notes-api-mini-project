from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from database import engine, Base, get_db
from models import User, Note

app = FastAPI(
    title="FastAPI User Notes API"
)

Base.metadata.create_all(bind=engine)


# -------------------------
# Pydantic Models
# -------------------------

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    user_id: int

    class Config:
        orm_mode = True


# -------------------------
# Create User
# -------------------------

@app.post(
    "/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user_in.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password=user_in.password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# -------------------------
# Create Note for User
# -------------------------

@app.post(
    "/users/{user_id}/notes/",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED
)
def create_note_for_user(
    user_id: int,
    note_in: NoteCreate,
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

    new_note = Note(
        title=note_in.title,
        content=note_in.content,
        user_id=user_id
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return new_note


# -------------------------
# Get Notes of User
# -------------------------

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

    notes = db.query(Note).filter(
        Note.user_id == user_id
    ).all()

    return notes