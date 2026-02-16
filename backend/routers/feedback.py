"""
Feedback router: handles HTTP requests for feedback submission and retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from core.database import get_session
from core.security import (
    get_current_user_flexible,
)
from models.user import User
from repositories.feedback_repo import FeedbackRepository
from schemas.feedback import (
    FeedbackResponse,
    FeedbackSubmitRequest,
    FeedbackUpdateRequest,
    PriorityRequest,
)
from services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback"])


# -------------------------
# CREATE
# -------------------------


@router.post(
    "/submit",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_feedback(
    request: FeedbackSubmitRequest,
    current_user: User = Depends(
        get_current_user_flexible
    ),  # 🔐 accept cookie or bearer
    session: Session = Depends(get_session),
):
    """
    Submit feedback for the current authenticated user.
    """
    repo = FeedbackRepository(session)
    service = FeedbackService(repo)

    feedback = service.submit_feedback(
        user_id=current_user.id,
        content=request.content,
        category=request.category,
        priority=request.priority,
    )

    return FeedbackResponse.from_orm(feedback)


# -------------------------
# READ (PUBLIC)
# -------------------------

# Note: `GET /{feedback_id}` is defined after static routes to avoid
# accidental matching of static paths like '/me' to the dynamic parameter.


@router.get("/category/{category}", response_model=list[FeedbackResponse])
def get_feedback_by_category(
    category: str,
    session: Session = Depends(get_session),
):
    """
    Public read: feedback by category.
    """
    repo = FeedbackRepository(session)
    service = FeedbackService(repo)

    feedback_list = service.get_feedback_by_category(category)
    return [FeedbackResponse.from_orm(f) for f in feedback_list]


@router.get("/priority/{priority}", response_model=list[FeedbackResponse])
def get_feedback_by_priority(
    priority: str,
    session: Session = Depends(get_session),
):
    """
    Public read: feedback by priority.
    """
    repo = FeedbackRepository(session)
    service = FeedbackService(repo)

    feedback_list = service.get_feedback_by_priority(priority)
    return [FeedbackResponse.from_orm(f) for f in feedback_list]


# -------------------------
# READ (PRIVATE / USER-SCOPED)
# -------------------------


@router.get("/me", response_model=list[FeedbackResponse])
def get_my_feedback(
    current_user: User = Depends(get_current_user_flexible),  # use cookie if available
    session: Session = Depends(get_session),
):
    """
    Get feedback for the authenticated user only.
    Works for AuthContext / Dashboard.
    """
    repo = FeedbackRepository(session)
    service = FeedbackService(repo)

    feedback_list = service.get_user_feedback(current_user.id)
    return [FeedbackResponse.from_orm(f) for f in feedback_list]


# Alias endpoint for compatibility
@router.get("/my-feedback", response_model=list[FeedbackResponse])
def my_feedback(
    current_user: User = Depends(get_current_user_flexible),
    session: Session = Depends(get_session),
):
    """
    Alias for /feedback/me
    """
    return get_my_feedback(current_user=current_user, session=session)


# -------------------------
# READ (PUBLIC) - by ID
# -------------------------


@router.get("/{feedback_id}", response_model=FeedbackResponse)
def get_feedback_by_id(
    feedback_id: int,
    session: Session = Depends(get_session),
):
    """
    Public read: get a feedback entry by ID.
    """
    repo = FeedbackRepository(session)
    feedback = repo.get_feedback_by_id(feedback_id)

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    return FeedbackResponse.from_orm(feedback)


# -------------------------
# UPDATE
# -------------------------


@router.put("/{feedback_id}", response_model=FeedbackResponse)
def update_feedback(
    feedback_id: int,
    request: FeedbackUpdateRequest,
    current_user: User = Depends(
        get_current_user_flexible
    ),  # 🔐 JWT or cookie required
    session: Session = Depends(get_session),
):
    """
    Update feedback by ID (only owner).
    """
    repo = FeedbackRepository(session)
    service = FeedbackService(repo)

    feedback = service.update_feedback(
        feedback_id=feedback_id,
        user_id=current_user.id,  # 👈 ownership enforced in service
        content=request.content,
        category=request.category,
        priority=request.priority,
    )

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found or not authorized",
        )

    return FeedbackResponse.from_orm(feedback)


# -------------------------
# DELETE
# -------------------------


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(
    feedback_id: int,
    current_user: User = Depends(
        get_current_user_flexible
    ),  # 🔐 JWT or cookie required
    session: Session = Depends(get_session),
):
    """
    Delete feedback by ID (only owner).
    """
    repo = FeedbackRepository(session)
    service = FeedbackService(repo)

    success = service.delete_feedback(
        feedback_id=feedback_id,
        user_id=current_user.id,  # 👈 ownership enforced
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found or not authorized",
        )

    return None


# -------------------------
# ML / AUXILIARY (PUBLIC)
# -------------------------


@router.post("/priority")
def predict_priority(
    request: PriorityRequest,
):
    """
    Predict priority level for feedback text.
    Public endpoint (no auth needed).
    """
    return {
        "response": "Priority endpoint not implemented yet.",
        "text": request.text,
    }
