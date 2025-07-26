# =============================================================================
# Multi-stage Dockerfile for FastAPI Application
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base - Common dependencies and setup
# -----------------------------------------------------------------------------
FROM python:3.11-alpine AS base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    libffi-dev \
    openssl-dev \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN adduser -D -s /bin/sh appuser

# -----------------------------------------------------------------------------
# Stage 2: Dependencies - Install Python packages
# -----------------------------------------------------------------------------
FROM base AS dependencies

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 3: Development - For development environment
# -----------------------------------------------------------------------------
FROM dependencies AS development

# Install development dependencies
RUN pip install \
    black \
    flake8 \
    mypy \
    uvicorn[standard]

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Development command with hot reload
CMD ["python", "-m", "uvicorn", "app_api:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# -----------------------------------------------------------------------------
# Stage 4: Production Builder - Prepare production files
# -----------------------------------------------------------------------------
FROM dependencies AS prod-builder

# Install production server
RUN pip install gunicorn

# Copy application code
COPY --chown=appuser:appuser . .

# Copy Gunicorn configuration
COPY lib/interfaces/docker/gunicorn.conf.py .

# Remove unnecessary files for production
RUN find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find . -type f -name "*.pyc" -delete && \
    find . -type f -name "*.pyo" -delete && \
    rm -rf .git/ 2>/dev/null || true && \
    rm -rf .pytest_cache/ 2>/dev/null || true

# -----------------------------------------------------------------------------
# Stage 5: Production - Final production image
# -----------------------------------------------------------------------------
FROM python:3.11-alpine AS production

# Set working directory
WORKDIR /app

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENV=production \
    WORKERS=2 \
    LOG_LEVEL=info

# Install only runtime dependencies (no build tools)
RUN apk add --no-cache \
    libffi \
    openssl \
    wget \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN adduser -D -s /bin/sh appuser

# Copy Python packages from builder stage
COPY --from=prod-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=prod-builder /usr/local/bin /usr/local/bin

# Copy application code from builder stage
COPY --from=prod-builder --chown=appuser:appuser /app /app

# Create logs directory
RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Production command with fixed temp directory
CMD ["gunicorn", "app_api:app", "--worker-tmp-dir", "/dev/shm", "-c", "gunicorn.conf.py"]

# -----------------------------------------------------------------------------
# Stage 6: Debug - For debugging production issues
# -----------------------------------------------------------------------------
FROM production AS debug

# Switch back to root for debugging tools
USER root

# Install debugging tools
RUN apk add --no-cache \
    htop \
    strace \
    tcpdump \
    curl \
    netcat-openbsd \
    procps

# Install Python debugging tools
RUN pip install --no-cache-dir \
    ipython \
    pdb++ \
    memory-profiler \
    py-spy

# Switch back to app user
USER appuser

# Override with debug-friendly command (with temp dir fix)
CMD ["gunicorn", "app_api:app", "--worker-tmp-dir", "/dev/shm", "-c", "gunicorn.conf.py", "--log-level", "debug", "--access-logfile", "/app/logs/access.log", "--error-logfile", "/app/logs/error.log"]
