FROM python:3.14-slim AS builder
WORKDIR /app

RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev


FROM python:3.14-slim AS runtime
WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser . .
RUN chmod +x ./entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER appuser

ENTRYPOINT [ "./entrypoint.sh" ]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]