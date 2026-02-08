"""Database engine and session management."""
from sqlmodel import create_engine, Session, SQLModel
import os
from sqlalchemy import text

# Read from environment or use default for local development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///feedback.db"
)

# Engine setup
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    """Create all tables and perform minimal compatibility fixes.

    This function creates tables if missing and applies lightweight
    compatibility fixes for development (e.g. add missing columns in
    SQLite when the model evolved). It intentionally does not perform
    destructive migrations.
    """
    SQLModel.metadata.create_all(engine)

    # Minimal SQLite compatibility: ensure `priority` column exists on feedback
    # If the DB was created before the model added `priority`, add the column.
    try:
        if engine.dialect.name == "sqlite":
            with engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info('feedback')")).fetchall()
                columns = [row[1] for row in result]
                if "priority" not in columns:
                    # Add nullable TEXT column; safe no-op for existing data
                    conn.execute(text("ALTER TABLE feedback ADD COLUMN priority TEXT"))
    except Exception:
        # Don't raise during app startup for non-critical migration failures;
        # leave the error visible in logs if necessary.
        pass


def get_session():
    """
    Dependency injection provider for database sessions.
    Yields a session and ensures cleanup.
    """
    with Session(engine) as session:
        yield session
