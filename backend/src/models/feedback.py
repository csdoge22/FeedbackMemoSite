"""Feedback persistence model using SQLModel."""

from typing import Optional

from sqlmodel import Field, SQLModel


class Feedback(SQLModel, table=True):
    """
    SQLModel persistence model for Feedback table.

    Internal DB representation - NOT exposed directly via API.
    See schemas.feedback for API contracts.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    content: str
    category: Optional[str] = None
    priority: Optional[str] = None
