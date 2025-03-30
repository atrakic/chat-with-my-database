ARG PYTHON_VERSION=3.12

# Use a Python image with uv pre-installed
FROM python:${PYTHON_VERSION}-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN <<EOF
    uv --version
    python --version
EOF

ENV \
    UV_CACHE_DIR=/cache \
    UV_LINK_MODE=copy \
    UV_SYSTEM_PYTHON=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LOCKED=1 \
    UV_PROJECT_ENVIRONMENT=/app


WORKDIR /src
# 2-step install, first dependencies, then the project itself
#
# `UV_LOCKED=1` - makes sure the uv.lock file is in sync with `pyproject.toml`
# `UV_PROJECT_ENVIRONMENT=/app` - installs into non-venv structure in /app


# Install dependencies in their own layer
RUN --mount=type=cache,target=/cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-dev --no-editable --no-install-project

# Copy the project into the builder - COPY is affected by `.dockerignore`
COPY . /src

# Sync the project - it will be installed in /app/
RUN --mount=type=cache,target=/cache \
    uv sync --no-dev --no-editable

FROM python:${PYTHON_VERSION}-slim AS final
WORKDIR /app

COPY --from=builder --chown=app:app /app/ /app/
COPY --chown=app:app /src/main.py ./

# Place executables in the environment at the front of the path
ENV PATH="/app/bin:$PATH"

ENTRYPOINT ["python", "-m", "streamlit", "run", "main.py", "--browser.gatherUsageStats", "false", "--server.port=8501", "--server.address=0.0.0.0"]
