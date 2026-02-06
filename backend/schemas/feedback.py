"""Feedback request and response schemas for API contracts."""
from pydantic import BaseModel, Field
from typing import Optional


# Request Schemas
class FeedbackSubmitRequest(BaseModel):
    """Request body for submitting feedback."""
    content: str = Field(..., min_length=1)
    category: Optional[str] = None
    priority: Optional[str] = None


class FeedbackUpdateRequest(BaseModel):
    """Request body for updating feedback."""
    content: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None


class FeedbackFilterRequest(BaseModel):
    """Request body for filtering feedback."""
    category: str


class FeedbackFilterByPriorityRequest(BaseModel):
    """Request body for filtering feedback by priority."""
    priority: str


# Response Schemas
class FeedbackResponse(BaseModel):
    """Feedback response schema."""
    id: int
    user_id: int
    content: str
    category: Optional[str] = None
    priority: Optional[str] = None

    class Config:
        from_attributes = True


class PriorityRequest(BaseModel):
    """Request body for priority prediction."""
    text: str
