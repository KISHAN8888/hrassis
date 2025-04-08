# Use a minimal Python image
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Make sure Celery is in PATH
ENV PATH="/bin:$PATH"

# Copy application files
COPY . /app

# Install dependencies using uv
RUN uv sync --frozen --no-cache

# Expose port
EXPOSE 8000

# Run the FastAPI application
CMD ["uv", "run","uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 