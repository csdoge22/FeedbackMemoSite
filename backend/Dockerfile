# Backend Dockerfile for Render deployment
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create non-root user (security best practice)
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Use Gunicorn with Uvicorn worker for production
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--bind", "0.0.0.0:8000", "--workers", "2", "--log-level", "info"]
