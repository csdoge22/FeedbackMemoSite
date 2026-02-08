"""User request and response schemas for API contracts."""
from pydantic import BaseModel, Field


# Request Schemas
class UserRegisterRequest(BaseModel):
    """Request body for user registration."""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class UserLoginRequest(BaseModel):
    """Request body for user login."""
    username: str
    password: str


class UserUpdateRequest(BaseModel):
    """Request body for user profile updates."""
    username: str | None = None
    password: str | None = None


# Response Schemas
class UserResponse(BaseModel):
    """User response schema (does not expose hashed_password)."""
    id: int
    username: str

    class Config:
        from_attributes = True
