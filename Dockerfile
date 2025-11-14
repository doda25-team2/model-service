FROM python:3.12-slim

WORKDIR /backend

COPY . /backend/

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV PATH="/root/.local/bin:${PATH}"
RUN uv sync --frozen

EXPOSE 8081

CMD ["uv", "run",  "/backend/src/serve_model.py"]
