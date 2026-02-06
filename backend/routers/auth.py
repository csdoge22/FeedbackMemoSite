"""Auth router: handles HTTP requests for user registration and login."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from core.database import get_session
from core.security import get_current_user
from schemas.user import UserRegisterRequest, UserLoginRequest, UserResponse
from services.auth_service import AuthService
from repositories.user_repo import UserRepository


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: UserRegisterRequest,
    session: Session = Depends(get_session),
):
    """
    Register a new user.
    
    Responsibilities:
    - Parse and validate request (Pydantic handles this)
    - Inject dependencies (session)
    - Call service layer
    - Convert response to schema
    - Return HTTP response
    """
    try:
        repo = UserRepository(session)
        service = AuthService(repo)
        user = service.register_user(request.username, request.password)
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
    Authenticate user and return success message.
    
    TODO: Return JWT token here when auth is fully implemented.
    """
    repo = UserRepository(session)
    service = AuthService(repo)
    authenticated = service.authenticate_user(request.username, request.password)
    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return {"message": "Login successful"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user = Depends(get_current_user),
):
    """
    Get the current authenticated user's profile.
    
    Demonstrates auth dependency injection.
    """
    # In production, current_user will be validated from JWT
    return UserResponse(id=current_user.id, username=current_user.username)

