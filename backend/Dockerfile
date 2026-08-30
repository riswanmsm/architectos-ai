# backend/Dockerfile
# Install dependencies in the development image, then copy only the virtual
# environment into the minimal, shell-less runtime image.
FROM cgr.dev/chainguard/python:latest-dev AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY backend/requirements.txt ./
RUN python -m venv /app/venv

ENV PATH="/app/venv/bin:${PATH}"

RUN python -m pip install --no-cache-dir --requirement requirements.txt

FROM cgr.dev/chainguard/python:latest AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/venv/bin:${PATH}"

WORKDIR /app

COPY --from=build /app/venv /app/venv

# Copy only the application package. In particular, do not copy the local
# virtual environment or .env file into the image.
COPY --chown=nonroot:nonroot backend/app ./app
COPY --chown=nonroot:nonroot architectos_llm ./architectos_llm
COPY --chown=nonroot:nonroot config ./config

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=2)"]

# Override the base image's Python entrypoint and launch Uvicorn as a module.
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000"]
