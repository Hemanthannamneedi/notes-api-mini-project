
from fastapi import (
    FastAPI, Depends, HTTPException, status
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import User, Post
from schemas import (
    UserRegister, UserResponse, TokenResponse,
    PostCreate, PostResponse, PostUpdate
)
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, RoleChecker
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Day 39 - Role-Based Access & Ownership")

admin_checker = RoleChecker(["admin"])


@app.get("/")
def home():
    return {"message": "Day 39 RBAC and Ownership API"}


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        (User.email == data.email) |
        (User.username == data.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password)
        # role defaults to "user"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@app.post("/auth/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Enter the registered email in Swagger's username field.
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(user)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.get("/auth/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


# -------------------- POSTS --------------------

@app.post(
    "/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = Post(
        title=data.title,
        content=data.content,
        owner_id=current_user.id
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return post


@app.get("/posts", response_model=list[PostResponse])
def list_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Each user sees only their own posts.
    return db.query(Post).filter(
        Post.owner_id == current_user.id
    ).all()


@app.put("/posts/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(
        Post.id == post_id
    ).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    # Ownership check: only the owner can update.
    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can update only your own posts"
        )

    post.title = data.title
    post.content = data.content

    db.commit()
    db.refresh(post)

    return post


@app.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(
        Post.id == post_id
    ).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    # Ownership check: only the owner can delete.
    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can delete only your own posts"
        )

    db.delete(post)
    db.commit()

    return {"message": "Post deleted successfully"}


# -------------------- ADMIN-ONLY ROUTES --------------------

@app.get("/admin/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(admin_checker)
):
    return db.query(User).all()


@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_checker)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="Use a separate admin account to delete this account"
        )

    # Delete the user's posts first to avoid foreign-key issues.
    db.query(Post).filter(
        Post.owner_id == user.id
    ).delete(synchronize_session=False)

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}
