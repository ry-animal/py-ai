# Multi-stage build for Python AI backend
FROM python:3.11-slim as base

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install -e .

# Development stage
FROM base as dev
RUN uv pip install -e ".[dev,agent]"
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as prod

# Copy application code
COPY src/ src/
COPY scripts/ scripts/
COPY tests/ tests/

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
# Create cache directories with proper permissions
RUN mkdir -p /home/appuser/.cache && chown -R appuser:appuser /home/appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENV PYTHONPATH="/app/src:$PYTHONPATH"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Worker stage
FROM prod as worker
USER root
RUN uv pip install -e ".[agent]"
USER appuser
ENV PYTHONPATH="/app/src:$PYTHONPATH"
CMD ["celery", "-A", "app.tasks", "worker", "--loglevel=info"]
