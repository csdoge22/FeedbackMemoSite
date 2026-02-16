from sqlmodel import Session, delete

from core.database import engine
from models.feedback import Feedback
from models.user import User


def clear_database():
    """
    Clear all feedback and users from the database.
    For testing purposes only.
    """
    with Session(engine) as session:
        session.exec(delete(Feedback))  # Delete child records first
        session.exec(delete(User))  # Then delete parent records
        session.commit()
