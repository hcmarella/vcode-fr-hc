# Multi-stage: `dev` target matches today's docker-compose workflow
# (bind-mounted source, --reload). `prod` target is what CI builds and pushes
# to ECR for EKS -- no bind mount, gunicorn managing multiple uvicorn workers,
# non-root user. Same base layers, so local dev and prod never drift apart on
# OS packages or Python version.

FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY scripts ./scripts

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]

# ---- dev: used by docker-compose.yml (build target: dev) ----
FROM base AS dev

RUN pip install --no-cache-dir -e ".[dev,aws]"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- prod: used by terraform/ECR build + k8s deployments ----
FROM base AS prod

RUN pip install --no-cache-dir -e ".[prod,aws]" \
    && useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
