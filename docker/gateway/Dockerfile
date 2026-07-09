# ---- Build stage ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN uv sync --frozen --no-install-project

# ---- Runtime stage ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    default-mysql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r gateway && useradd -r -g gateway gateway

WORKDIR /app

COPY --from=builder /build/.venv /app/.venv
COPY . .

RUN chown -R gateway:gateway /app
USER gateway

ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/app \
    UV_CACHE_DIR=/app/.cache/uv

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5001/healthz || exit 1

CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "60", "app.wsgi:app"]