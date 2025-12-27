from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_db
from .schemas import FeedbackCreate, FeedbackRead
from . import crud

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}


# OMITTED until I get PostgreSQL working

# @app.post("/feedback", response_model=FeedbackRead)
# async def create_feedback(payload: FeedbackCreate, db: AsyncSession = Depends(get_db)):
#     return await crud.create_feedback(db, payload)

# @app.get("/feedback", response_model=list[FeedbackRead])
# async def list_feedback(db: AsyncSession = Depends(get_db)):
#     return await crud.get_feedbacks(db)
