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

from utils import database
from core.database import create_db_and_tables
from routers import auth, feedback


app = FastAPI(
    title="Feedback API",
    version="1.0.0",
    description="API for managing user feedback with authentication",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.getenv("ENV")=="dev":
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

