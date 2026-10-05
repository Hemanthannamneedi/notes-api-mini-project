from fastapi import FastAPI
from database import engine, Base
import models

app = FastAPI(
    title="FastAPI Database Models"
)

Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {
        "message": "User and Note tables created successfully"
    }