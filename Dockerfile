# syntax=docker/dockerfile:1

# ─── Stage 1: Build frontend ────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ─── Stage 2: Run backend + serve static files ────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install system deps for yfinance / pandas / aiosqlite
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source into /app so module path "app.main" resolves correctly
COPY backend/ .

# Copy built frontend dist into app/static (where main.py looks for it)
COPY --from=frontend-builder /frontend/dist ./app/static

# Set environment
ENV PYTHONPATH=/app
ENV PORT=8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
