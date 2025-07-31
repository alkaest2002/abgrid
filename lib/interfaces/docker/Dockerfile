# Build stage - install fonts
FROM python:3.13-alpine as font-builder

RUN apk add --no-cache \
    fontconfig \
    ttf-dejavu \
    ttf-liberation \
    msttcorefonts-installer \
    wget && \
    update-ms-fonts && \
    fc-cache -f

# Build stage - install Python deps
FROM python:3.13-alpine as python-builder

RUN apk add --no-cache gcc g++ musl-dev linux-headers libffi-dev openssl-dev build-base

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.13-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENV=production \
    FONTCONFIG_PATH=/etc/fonts

# Install minimal runtime dependencies
RUN apk add --no-cache fontconfig wget && \
    adduser -D -s /bin/sh appuser && \
    rm -rf /var/cache/apk/*

# Copy fonts from font-builder (only the actual font files)
COPY --from=font-builder /usr/share/fonts/ /usr/share/fonts/
COPY --from=font-builder /etc/fonts/ /etc/fonts/

# Copy Python packages from python-builder
COPY --from=python-builder /root/.local /home/appuser/.local

# Rebuild font cache and cleanup
RUN fc-cache -f && \
    rm -rf /var/cache/fontconfig/*

# Copy application
COPY --chown=appuser:appuser app_api.py .
COPY --chown=appuser:appuser lib/ ./lib/
COPY --chown=appuser:appuser lib/interfaces/docker/gunicorn.conf.py .

RUN mkdir -p logs && chown appuser:appuser logs

USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:8000/health || exit 1

CMD ["gunicorn", "app_api:app", "--worker-tmp-dir", "/dev/shm", "-c", "gunicorn.conf.py"]
