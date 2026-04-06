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

from src.routers import auth
from src.core.database import create_db_and_tables
from src.routers import feedback
from src.utils import database

# --------------------------
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
# In production set CORS_ORIGINS to your deployed frontend URL(s), e.g. https://your-app.vercel.app
ENV = os.getenv("ENV", "dev")

if ENV == "dev":
    # Local frontend development
    CORS_ORIGINS = ["http://localhost:5173"]
else:
    # Production — placeholder until frontend is hosted
    CORS_ORIGINS = ["*"]  # temporarily allow all origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.getenv("ENV") == "dev":
    database.clear_database()

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
