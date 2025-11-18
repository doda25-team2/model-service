FROM python:3.12-slim AS builder
WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

FROM python:3.12-slim
WORKDIR /backend
VOLUME ["/models"]

ENV MODEL_PATH=/models/model.joblib
ENV PREPROCESSOR_PATH=/models/preprocessor.joblib
ENV DEFAULT_MODEL_URL="https://github.com/doda25-team2/model-service/releases/latest/download/model.joblib"
ENV DEFAULT_PREPROCESSOR_URL="https://github.com/doda25-team2/model-service/releases/latest/download/preprocessor.joblib"

COPY --from=builder /build/.venv /backend/.venv
COPY src/ /backend/src/
ENV PATH="/backend/.venv/bin:$PATH"
EXPOSE 8081
CMD ["python", "/backend/src/serve_model.py"]
