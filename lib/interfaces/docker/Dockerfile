FROM python:3.11-alpine

WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENV=production

# Install dependencies
RUN apk add --no-cache gcc musl-dev linux-headers libffi-dev openssl-dev wget && \
    adduser -D -s /bin/sh appuser

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY --chown=appuser:appuser . .
COPY lib/interfaces/docker/gunicorn.conf.py .

# Cleanup
RUN find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find . -name "*.pyc" -delete && \
    rm -rf .git tests .vscode lib/interfaces/docker 2>/dev/null || true && \
    mkdir -p logs && chown appuser:appuser logs

# Runtime dependencies only
RUN apk del gcc musl-dev linux-headers && \
    rm -rf /var/cache/apk/*

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:8000/health || exit 1

CMD ["gunicorn", "app_api:app", "--worker-tmp-dir", "/dev/shm", "-c", "gunicorn.conf.py"]
