from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Feedback
from .schemas import FeedbackCreate, FeedbackRead

async def create_feedback(db: AsyncSession, payload: FeedbackCreate) -> FeedbackRead:
    feedback = Feedback(title=payload.title, content=payload.content)
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    # Explicit conversion for type safety
    return FeedbackRead.from_orm(feedback)

async def get_feedbacks(db: AsyncSession) -> list[FeedbackRead]:
    result = await db.execute(select(Feedback))
    feedbacks = result.scalars().all()
    return [FeedbackRead.from_orm(f) for f in feedbacks]
