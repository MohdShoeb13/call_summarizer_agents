# Multi-stage build for call_summarizer_agents.
# Stage 1 builds the React frontend; stage 2 runs the FastAPI backend, which
# serves the built SPA from frontend/dist (same-origin, no separate frontend
# host needed).

# --- Stage 1: build the frontend -------------------------------------------
FROM node:22-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python backend -----------------------------------------------
FROM python:3.12-slim
WORKDIR /app

# uv for fast, locked installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ ./backend/
COPY data/ ./data/
# Bring in the built SPA so the backend can serve it.
COPY --from=frontend /app/frontend/dist ./frontend/dist

# SQLite lives on a mounted disk in production (see render.yaml).
ENV DATABASE_PATH=/data/calls.sqlite3
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8018
# Render provides $PORT; default to 8018 for local `docker run`.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8018}"]
