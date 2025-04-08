# Base image
FROM python:3.12-slim AS worker

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

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-cache

# Copy application code
COPY . .

# Make sure Celery is in PATH
ENV PATH="/bin:$PATH"

# Command to run Celery worker
ENTRYPOINT ["uv", "run", "celery"]
CMD ["-A", "app.tasks.celery_app", "worker", "--loglevel=info"]