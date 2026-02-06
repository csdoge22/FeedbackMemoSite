"""Feedback router: handles HTTP requests for feedback submission and retrieval."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from core.database import get_session
from core.security import get_current_user
from schemas.feedback import FeedbackSubmitRequest, FeedbackResponse, PriorityRequest
from services.feedback_service import FeedbackService
from repositories.feedback_repo import FeedbackRepository


router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("/submit", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    request: FeedbackSubmitRequest,
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Submit feedback for the current authenticated user.
    
    Responsibilities:
    - Parse and validate request (Pydantic handles this)
    - Inject dependencies (session, current_user)
    - Call service layer
    - Convert response to schema
    - Return HTTP response
    """
    try:
        repo = FeedbackRepository(session)
        service = FeedbackService(repo)
        feedback = service.submit_feedback(
            user_id=current_user.id,
            content=request.content,
            category=request.category,
        )
        return FeedbackResponse.from_orm(feedback)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/user/{user_id}", response_model=list[FeedbackResponse])
def get_user_feedback(
    user_id: int,
    session: Session = Depends(get_session),
):
    """
    Get all feedback submitted by a specific user.
    """
    repo = FeedbackRepository(session)
    service = FeedbackService(repo)
    feedback_list = service.get_user_feedback(user_id)
    return [FeedbackResponse.from_orm(f) for f in feedback_list]


@router.get("/category/{category}", response_model=list[FeedbackResponse])
def get_feedback_by_category(
    category: str,
    session: Session = Depends(get_session),
):
    """
    Get all feedback for a specific category.
    """
    repo = FeedbackRepository(session)
    service = FeedbackService(repo)
    feedback_list = service.get_feedback_by_category(category)
    return [FeedbackResponse.from_orm(f) for f in feedback_list]


@router.delete("/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(
    feedback_id: int,
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Delete feedback by ID (only for authenticated users).
    """
    repo = FeedbackRepository(session)
    service = FeedbackService(repo)
    success = service.delete_feedback(feedback_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )
    return None


@router.post("/priority")
def get_priority(
    request: PriorityRequest,
):
    """
    Predict priority level for feedback text.
    
    TODO: Integrate with ML model.
    """
    return {
        "response": "Priority endpoint not implemented yet.",
        "text": request.text,
    }

