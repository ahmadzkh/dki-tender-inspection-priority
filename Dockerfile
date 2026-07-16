FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PROJECT_ROOT=/app \
    CORS_ORIGINS=http://localhost:3000

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md .python-version ./
COPY src ./src
RUN uv sync --frozen --no-dev

COPY backend ./backend
COPY artifacts ./artifacts
COPY datasets/processed ./datasets/processed
COPY reports/model/evaluation.json ./reports/model/evaluation.json

RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).read()"

CMD ["/app/.venv/bin/uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
