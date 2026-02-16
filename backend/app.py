"""
FastAPI application entry point.

This file:
- Instantiates the FastAPI app
- Initializes database tables
- Registers routers
- Serves as the ASGI entry point
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import create_db_and_tables
from routers import auth, feedback
from utils import database

# -------------------------
# STARTUP VALIDATION
# -------------------------


def validate_environment():
    """Validate required environment variables at startup."""
    required_vars = ["SECRET_KEY", "ALGORITHM", "ENV"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please check your .env file."
        )


validate_environment()

app = FastAPI(
    title="Feedback API",
    version="1.0.0",
    description="API for managing user feedback with authentication",
)

# Configure CORS with environment-specific origins
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables on startup (safe no-op if already present)
create_db_and_tables()

if os.getenv("ENV") == "dev":
    database.clear_database()

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
