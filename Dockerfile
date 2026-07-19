# ── P2-20: Multi-stage Dockerfile for Mantle Intel Agent ──────────────────────
# Build:  docker build -t mantle-intel-agent .
# Run:    docker run -p 8000:8000 --env-file .env mantle-intel-agent

# Stage 1: Base with Python
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# P2-16: OpenTelemetry dependencies (optional but recommended)
RUN pip install --no-cache-dir \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-exporter-otlp 2>/dev/null || true

# P2-19: Rate limiting dependency
RUN pip install --no-cache-dir slowapi 2>/dev/null || true

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
