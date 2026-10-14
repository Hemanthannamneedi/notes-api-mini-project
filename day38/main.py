
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import Base, engine, get_db
from models import User, Post, Comment
from schemas import (
    UserRegister,
    UserResponse,
    TokenResponse,
    PostCreate,
    PostResponse,
    CommentCreate,
    CommentResponse,
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Day 38 - Protected Routes")


@app.get("/")
def home():
    return {"message": "Day 38 Protected Routes API is running"}


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(
        (User.username == user_data.username)
        | (User.email == user_data.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
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
            status_code=409,
            detail="Username or email already registered"
        )


@app.post("/auth/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # OAuth2 form field "username" contains the user's email.
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if (
        user is None
        or not verify_password(
            form_data.password,
            user.hashed_password
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer"
    }


@app.get("/auth/me", response_model=UserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return current_user


# ---------------- PROTECTED POSTS ----------------

@app.post(
    "/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
def create_post(
    post_data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = Post(
        title=post_data.title,
        content=post_data.content,
        owner_id=current_user.id
    )

    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@app.get("/posts", response_model=list[PostResponse])
def get_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Post).filter(
        Post.owner_id == current_user.id
    ).all()


@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.owner_id == current_user.id
    ).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


# ---------------- PROTECTED COMMENTS ----------------

@app.post(
    "/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_comment(
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(
        Post.id == comment_data.post_id
    ).first()

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    comment = Comment(
        content=comment_data.content,
        post_id=post.id,
        owner_id=current_user.id
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@app.get("/comments", response_model=list[CommentResponse])
def get_comments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Comment).filter(
        Comment.owner_id == current_user.id
    ).all()


@app.get(
    "/posts/{post_id}/comments",
    response_model=list[CommentResponse]
)
def get_post_comments(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.owner_id == current_user.id
    ).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return db.query(Comment).filter(
        Comment.post_id == post_id
    ).all()
