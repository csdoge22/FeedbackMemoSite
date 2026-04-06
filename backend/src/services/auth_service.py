"""Auth service: contains business logic for user registration and authentication."""

from core.security import hash_password, verify_password
from models.user import User
from repositories.user_repo import UserRepository


class AuthService:
    """
    AuthService contains all authentication business logic.

    Responsibilities:
    - User registration logic (check duplicates, hash password)
    - User authentication (verify credentials)
    - User management (get, update, delete)

    Does NOT:
    - Create database sessions
    - Handle HTTP requests
    - Access FastAPI
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register_user(self, username: str, password: str) -> User:
        """
        Register a new user with username and password.

        Raises ValueError if username already exists.
        """
        existing_user = self.user_repo.get_by_username(username)
        if existing_user:
            raise ValueError("Username already exists")
        hashed = hash_password(password)
        user = User(username=username, hashed_password=hashed)
        return self.user_repo.save(user)

    def authenticate_user(self, username: str, password: str) -> User | None:
        """Authenticate user credentials. Returns User if valid, else None."""
        user = self.user_repo.get_by_username(username)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    def get_user(self, user_id: int) -> User | None:
        """Get a user by ID."""
        return self.user_repo.get_by_id(user_id)

    def update_user(
        self,
        user_id: int,
        username: str | None = None,
        password: str | None = None,
    ) -> User | None:
        """Update user username or password."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        if username:
            user.username = username
        if password:
            user.hashed_password = hash_password(password)
        return self.user_repo.update(user)

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False
        return self.user_repo.delete(user)
