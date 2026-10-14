
import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User


SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    SECRET_KEY = "local-practice-only-change-this-secret-key"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

oauth2_bearer = OAuth2PasswordBearer(
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

    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        "iat": now,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def get_current_user(
    token: str = Depends(oauth2_bearer),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate user",
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
