"""
Auth router: handles HTTP requests for user registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlmodel import Session
from dotenv import load_dotenv
import os

from core.database import get_session
from core.security import get_current_user, create_jwt_token, get_current_user_from_cookie, get_current_user_flexible
from schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
)
from services.auth_service import AuthService
from repositories.user_repo import UserRepository

load_dotenv()
router = APIRouter(prefix="/auth", tags=["Auth"])
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: UserRegisterRequest,
    session: Session = Depends(get_session),
):
    """
    Register a new user.

    Flow:
    Router -> Service -> Repo -> DB
    """
    try:
        repo = UserRepository(session)
        service = AuthService(repo)

        user = service.register_user(
            username=request.username,
            password=request.password,
        )

        return UserResponse.from_orm(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login")
def login(
    request: UserLoginRequest,
    response: Response,  # <- added
    session: Session = Depends(get_session),
):
    repo = UserRepository(session)
    service = AuthService(repo)

    user = service.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_jwt_token(user)

    # Set JWT in HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",  # or 'strict' in production
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,  # True if using HTTPS
    )

    return {"message": "Login successful"}

@router.post("/logout")
def logout(response: Response):
    """
    Logout endpoint - removes the HTTP-only JWT cookie.
    """
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user=Depends(get_current_user_flexible),
):
    """
    Get the current authenticated user's profile.
    Works with both HTTP-only cookie and Authorization Bearer header.
    """
    return UserResponse.from_orm(current_user)