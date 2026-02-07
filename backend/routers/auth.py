"""
Auth router: handles HTTP requests for user registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from core.database import get_session
from core.security import get_current_user, create_jwt_token
from schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
)
from services.auth_service import AuthService
from repositories.user_repo import UserRepository

router = APIRouter(prefix="/auth", tags=["Auth"])


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


@router.post("/login", status_code=status.HTTP_200_OK)
def login(
    request: UserLoginRequest,
    session: Session = Depends(get_session),
):
    """
    Authenticate user and return JWT token.

    Flow:
    - Validate credentials
    - Issue JWT
    - Frontend stores token and sends it on future requests
    """
    repo = UserRepository(session)
    service = AuthService(repo)

    user = service.authenticate_user(
        username=request.username,
        password=request.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_jwt_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user=Depends(get_current_user),
):
    """
    Get the current authenticated user's profile.

    Requires:
    Authorization: Bearer <JWT>
    """
    return UserResponse.from_orm(current_user)
