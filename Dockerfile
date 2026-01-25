# Multi-stage Dockerfile for the SMS Spam Detection Model Service
# Supports F3 (Containerization), F4 (Multi-architecture), F5 (Multi-stage)

FROM python:3.12-slim AS builder
WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

FROM python:3.12-slim
WORKDIR /backend

# Model compatibility labels (for documentation and tooling)
LABEL org.opencontainers.image.title="SMS Spam Model Service"
LABEL org.opencontainers.image.description="ML model service for SMS spam detection"
LABEL org.opencontainers.image.source="https://github.com/doda25-team2/model-service"
LABEL model.min-version="Model-v1.0.0"
LABEL model.format="joblib"
LABEL model.input-schema="text_string"
LABEL model.output-schema="ham_or_spam"

# Volume for model files (F10: Decoupled Model)
VOLUME ["/models"]

# Model configuration - can be overridden at runtime
ENV MODEL_PATH=/models/model.joblib
ENV PREPROCESSOR_PATH=/models/preprocessor.joblib
ENV METADATA_PATH=/models/model_metadata.json

# Default model URLs - downloads latest model on startup if not mounted
ENV DEFAULT_MODEL_URL="https://github.com/doda25-team2/model-service/releases/latest/download/model.joblib"
ENV DEFAULT_PREPROCESSOR_URL="https://github.com/doda25-team2/model-service/releases/latest/download/preprocessor.joblib"
ENV DEFAULT_METADATA_URL="https://github.com/doda25-team2/model-service/releases/latest/download/model_metadata.json"

# Service version - should be updated by CI/CD during release
# This allows runtime version reporting via /health endpoint
ARG SERVICE_VERSION=v1.0.0
ENV SERVICE_VERSION=${SERVICE_VERSION}

# Copy virtual environment and source code
COPY --from=builder /build/.venv /backend/.venv
COPY src/ /backend/src/
ENV PATH="/backend/.venv/bin:$PATH"

# Port configuration (F6: Flexible Containers)
ENV MODEL_SERVICE_PORT=8081
EXPOSE 8081

CMD ["python", "/backend/src/serve_model.py"]
