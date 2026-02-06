"""Security utilities and auth dependency stubs."""
from passlib.context import CryptContext
from fastapi import Depends
from sqlmodel import Session

from core.database import get_session
from repositories.user_repo import UserRepository
from models.user import User

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


# Stubbed auth dependency - will be replaced with JWT later
class CurrentUserStub:
    """Stub current user object. Replace with JWT-based auth later."""
    def __init__(self, user_id: int = 1, username: str = "testuser"):
        self.id = user_id
        self.username = username


def get_current_user(
    session: Session = Depends(get_session),
) -> CurrentUserStub:
    """
    Dependency to get the current authenticated user.
    
    STUB: Currently returns a fake user.
    TODO: Replace with JWT token validation.
    Design allows services to use this without changes.
    """
    # Stub: Return a fake authenticated user
    # In production, validate JWT token from request headers
    return CurrentUserStub(user_id=1, username="testuser")
