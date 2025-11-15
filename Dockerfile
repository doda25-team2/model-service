FROM python:3.12-slim AS builder
WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

FROM python:3.12-slim
WORKDIR /backend
COPY --from=builder /build/.venv /backend/.venv
COPY src/ /backend/src/
COPY output/ /backend/output/
ENV PATH="/backend/.venv/bin:$PATH"
EXPOSE 8081
CMD ["python", "/backend/src/serve_model.py"]
