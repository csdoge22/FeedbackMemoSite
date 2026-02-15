"""
Security utilities and authentication dependencies.
Handles:
- Password hashing
- JWT creation and validation
- FastAPI dependency injection for authenticated users
- Support for both Authorization header and HTTP-only cookie
"""

from datetime import datetime, timedelta
from typing import Optional
import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from sqlmodel import Session

from core.database import get_session
from repositories.user_repo import UserRepository
from models.user import User

load_dotenv()

# -------------------------
# CONFIG
# -------------------------

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

ALGORITHM = os.getenv("ALGORITHM")
if not ALGORITHM:
    raise ValueError("ALGORITHM environment variable is required")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# -------------------------
# PASSWORD HASHING
# -------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


# -------------------------
# JWT SETUP
# -------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_jwt_token(user: User) -> str:
    """
    Create a JWT access token for a user with expiration.
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# -------------------------
# AUTH DEPENDENCIES
# -------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """
    Dependency to get the currently authenticated user from an Authorization Bearer token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    except JWTError:
        raise credentials_exception

    repo = UserRepository(session)
    user = repo.get_by_id(int(user_id))
    if not user:
        raise credentials_exception

    return user


def get_current_user_from_cookie(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    """
    Dependency to get the currently authenticated user from an HTTP-only cookie.
    Cookie name must match frontend (e.g., 'access_token').
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication cookie not found",
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    repo = UserRepository(session)
    user = repo.get_by_id(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user

def get_current_user_flexible(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    """
    Dependency to get the currently authenticated user.
    Works with:
      1. HTTP-only cookie: 'access_token'
      2. Authorization Bearer header
    """
    token = request.cookies.get("access_token")

    # If cookie not present, check Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer ") :]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

    # Decode JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
        )

    # Fetch user from DB
    repo = UserRepository(session)
    user = repo.get_by_id(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
