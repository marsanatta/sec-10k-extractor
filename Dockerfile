# --- Stage 1: build the React SPA ---
FROM node:20-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm ci || npm install
COPY web/ ./
RUN npm run build

# --- Stage 2: Python API serving the built SPA ---
FROM python:3.11-slim
WORKDIR /app

COPY pyproject.toml ./
COPY sec10k/ ./sec10k/
COPY api/ ./api/
COPY eval/report.md ./eval/report.md
RUN pip install --no-cache-dir ".[api,llm]"

COPY --from=web /web/dist ./web/dist

EXPOSE 8000
# SEC_EDGAR_USER_AGENT must be provided at runtime (-e); the API returns a 500 if unset.
# Bind $PORT when the platform injects one (Zeabur / Azure / Railway), else default 8000.
# `exec` so uvicorn is PID 1 and receives SIGTERM on container stop.
CMD ["sh", "-c", "exec uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
