"""User repository: database access layer for User model."""
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from models.user import User


class UserRepository:
    """
    UserRepository handles all database operations for User model.
    
    Responsibilities:
    - CRUD operations (Create, Read, Update, Delete)
    - Execute SQLModel queries
    - Translate DB errors to domain errors
    
    Does NOT:
    - Contain business logic
    - Import FastAPI
    - Create sessions
    """

    def __init__(self, session: Session):
        self.session = session

    def save(self, user: User) -> User:
        """
        Save a new user to the database.
        
        Raises ValueError if username already exists (duplicate key).
        """
        self.session.add(user)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            # Translate DB error to domain error
            raise ValueError("Username already exists")
        self.session.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> User | None:
        """Get a user by ID."""
        statement = select(User).where(User.id == user_id)
        return self.session.exec(statement).first()

    def get_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        statement = select(User).where(User.username == username)
        return self.session.exec(statement).first()

    def update(self, user: User) -> User:
        """Update an existing user."""
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user: User) -> bool:
        """Delete a user."""
        self.session.delete(user)
        self.session.commit()
        return True

