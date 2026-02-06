"""
FastAPI application entry point.

This file:
- Instantiates the FastAPI app
- Initializes database tables
- Registers routers
- Serves as the ASGI entry point
"""
from fastapi import FastAPI

from core.database import create_db_and_tables
from routers import auth, feedback


app = FastAPI(
    title="Feedback API",
    version="1.0.0",
    description="API for managing user feedback with authentication",
)

# Initialize database tables on startup (safe no-op if already present)
create_db_and_tables()

# Register routers for modular endpoint organization
app.include_router(auth.router)
app.include_router(feedback.router)


@app.get("/")
def index():
    """Health check endpoint."""
    return {"response": "Welcome to the Feedback API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """Simple health check for monitoring."""
    return {"status": "ok"}

