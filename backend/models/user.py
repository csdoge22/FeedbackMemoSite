"""User persistence model using SQLModel."""
from sqlmodel import SQLModel, Field
from typing import Optional


class User(SQLModel, table=True):
    """
    SQLModel persistence model for User table.
    
    Combines SQLAlchemy ORM with Pydantic validation.
    Internal DB representation - NOT exposed directly via API.
    See schemas.user for API contracts.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
