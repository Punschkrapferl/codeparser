# Dockerfile.backend
FROM python:3.12-slim

# System deps: git for clone, go for parser_go, build tools for any wheels
RUN apt-get update && apt-get install -y \
      git \
      golang \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) Copy only requirements first for better build caching
COPY api/requirements.txt ./api/requirements.txt

# 2) Install Python dependencies (+ pytest for running tests inside container)
RUN pip install --no-cache-dir -r api/requirements.txt \
    && pip install --no-cache-dir pytest

# 3) Copy backend code
COPY api ./api
COPY parser_go ./parser_go
COPY codeparser ./codeparser
COPY pytest.ini ./pytest.ini
COPY __init__.py ./__init__.py

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# 4) Create repos dir (also mounted from host via docker-compose)
RUN mkdir -p /app/repos

EXPOSE 8000

# 5) FastAPI entrypoint
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
