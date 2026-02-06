"""Feedback repository: database access layer for Feedback model."""
from sqlmodel import Session, select
from models.feedback import Feedback


class FeedbackRepository:
    """
    FeedbackRepository handles all database operations for Feedback model.
    
    Responsibilities:
    - CRUD operations (Create, Read, Update, Delete)
    - Execute SQLModel queries
    
    Does NOT:
    - Contain business logic
    - Import FastAPI
    - Create sessions
    """

    def __init__(self, session: Session):
        self.session = session

    def save_feedback(self, feedback: Feedback) -> Feedback:
        """Save a new feedback entry to the database."""
        self.session.add(feedback)
        self.session.commit()
        self.session.refresh(feedback)
        return feedback

    def get_feedback_by_user(self, user_id: int) -> list[Feedback]:
        """Get all feedback submitted by a specific user."""
        statement = select(Feedback).where(Feedback.user_id == user_id)
        return self.session.exec(statement).all()

    def get_feedback_by_category(self, category: str) -> list[Feedback]:
        """Get all feedback for a specific category."""
        statement = select(Feedback).where(Feedback.category == category)
        return self.session.exec(statement).all()

    def delete_feedback(self, feedback_id: int) -> bool:
        """Delete feedback by ID. Returns True if found and deleted, False otherwise."""
        statement = select(Feedback).where(Feedback.id == feedback_id)
        feedback = self.session.exec(statement).first()
        if feedback:
            self.session.delete(feedback)
            self.session.commit()
            return True
        return False
