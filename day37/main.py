

import os
from datetime import datetime, timedelta, timezone

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from jose import jwt, JWTError

from database import Base, engine, get_db
from models import User
from auth_schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenData,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Day 37 - JWT Token Generation")

# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    SECRET_KEY = "local-practice-only-change-this-secret-key"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
        "iat": now,
        "exp": expires_at,
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        raise credentials_exception

    return user


@app.get("/")
def home():
    return {
        "message": "Day 37 JWT Authentication API is running"
    }


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        (User.email == user_data.email)
        | (User.username == user_data.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered"
        )

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered"
        )


@app.post(
    "/auth/login",
    response_model=TokenResponse
)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == login_data.email
    ).first()

    if (
        user is None
        or not verify_password(
            login_data.password,
            user.hashed_password
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.get(
    "/auth/me",
    response_model=UserResponse
)
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return current_user
