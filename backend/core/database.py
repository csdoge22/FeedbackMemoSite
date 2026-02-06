"""Database engine and session management."""
from sqlmodel import create_engine, Session, SQLModel
import os

# Read from environment or use default for local development
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///feedback.db"
)

# SQLite setup
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        DATABASE_URL,
        echo=False
    )


def create_db_and_tables():
    """Create all tables in the database. Safe no-op if already present."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Dependency injection provider for database sessions.
    Yields a session and ensures cleanup.
    """
    with Session(engine) as session:
        yield session
