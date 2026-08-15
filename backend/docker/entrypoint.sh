#!/bin/sh
set -e

# Local/dev (docker-compose) runs migrations on every boot for convenience --
# fine with a single replica. Prod (EKS) sets RUN_MIGRATIONS_ON_BOOT=false and
# runs `alembic upgrade head` once via a k8s Job before the rollout instead,
# so N replicas starting together don't race each other altering the schema.
if [ "${RUN_MIGRATIONS_ON_BOOT:-true}" = "true" ]; then
  alembic upgrade head
fi

exec "$@"
