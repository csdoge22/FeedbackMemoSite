"""Feedback service: contains business logic for feedback submission and retrieval."""
from models.feedback import Feedback
from repositories.feedback_repo import FeedbackRepository


class FeedbackService:
    """
    FeedbackService contains all feedback-related business logic.
    
    Responsibilities:
    - Validate and submit feedback
    - Retrieve feedback by user or category
    - Delete feedback
    
    Does NOT:
    - Create database sessions
    - Handle HTTP requests
    - Access FastAPI
    """

    def __init__(self, feedback_repo: FeedbackRepository):
        self.feedback_repo = feedback_repo

    def submit_feedback(
        self,
        user_id: int,
        content: str,
        category: str | None = None,
    ) -> Feedback:
        """
        Submit feedback for a user.
        
        Returns the created Feedback object.
        """
        feedback = Feedback(
            user_id=user_id,
            content=content,
            category=category,
        )
        return self.feedback_repo.save_feedback(feedback)

    def get_user_feedback(self, user_id: int) -> list[Feedback]:
        """Get all feedback submitted by a user."""
        return self.feedback_repo.get_feedback_by_user(user_id)

    def get_feedback_by_category(self, category: str) -> list[Feedback]:
        """Get all feedback for a specific category."""
        return self.feedback_repo.get_feedback_by_category(category)

    def delete_feedback(self, feedback_id: int) -> bool:
        """Delete feedback by ID. Returns True if successful, False if not found."""
        return self.feedback_repo.delete_feedback(feedback_id)
