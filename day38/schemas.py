
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    owner_id: int


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)
    post_id: int


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    post_id: int
    owner_id: int
