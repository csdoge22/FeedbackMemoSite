"""Database engine and session management with PostgreSQL support."""
from sqlmodel import create_engine, Session, SQLModel
import os

# Read from environment or use default PostgreSQL for local development
# Default: PostgreSQL on localhost using current user (macOS Homebrew)
# For production, set DATABASE_URL environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost/feedbackdb"
)

# Engine setup for PostgreSQL
# Using psycopg2-binary as the driver (installed in requirements.txt)
engine = create_engine(
    DATABASE_URL,
    echo=False,
    # Connection pool settings optimized for development
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using them
)


def create_db_and_tables():
    """Create all tables in PostgreSQL.

    This function creates all SQLModel tables if they don't already exist.
    Safe to call multiple times (idempotent).
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Dependency injection provider for database sessions.
    Yields a session and ensures cleanup.
    """
    with Session(engine) as session:
        yield session
