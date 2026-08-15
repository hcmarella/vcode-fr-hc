"""Queue abstraction for handing a PENDING SyncRun off to a worker.

Two backends, selected by settings.sync_queue_backend:

- postgres (default, used by docker-compose/local dev): enqueue() is a no-op.
  The worker polls the sync_runs table directly with SELECT ... FOR UPDATE
  SKIP LOCKED, so no message actually needs to move anywhere -- the DB row
  itself *is* the queue. Zero extra infrastructure, safe across multiple
  worker replicas (SKIP LOCKED guarantees each row is claimed once).

- sqs (used on EKS/prod, see terraform/sqs.tf): enqueue() sends a message
  naming the run id. The worker long-polls SQS instead of hammering Postgres
  with polling queries, and gets built-in retry via SQS's visibility timeout
  if a worker pod dies mid-job. This is the backend to use once sync volume
  or team count makes DB polling wasteful.

Swapping is a one-line env var change (SYNC_QUEUE_BACKEND), not a code change
-- the worker's claim loop is backend-specific but both live in
app/workers/sync_worker.py behind the same run() entrypoint.
"""

import asyncio
import uuid
from functools import lru_cache
from typing import Protocol

from app.config import get_settings


class SyncQueue(Protocol):
    async def enqueue(self, sync_run_id: uuid.UUID) -> None: ...


class PostgresPollQueue:
    async def enqueue(self, sync_run_id: uuid.UUID) -> None:
        return None  # the worker discovers pending rows by polling; nothing to send


class SQSQueue:
    def __init__(self, queue_url: str, region: str):
        import boto3  # imported lazily -- only needed when this backend is selected

        self._queue_url = queue_url
        self._client = boto3.client("sqs", region_name=region)

    async def enqueue(self, sync_run_id: uuid.UUID) -> None:
        # boto3 is synchronous; run it off the event loop so a slow SQS call
        # doesn't block other requests being served by this worker/process.
        await asyncio.to_thread(
            self._client.send_message,
            QueueUrl=self._queue_url,
            MessageBody=str(sync_run_id),
        )


@lru_cache
def get_sync_queue() -> SyncQueue:
    settings = get_settings()
    if settings.sync_queue_backend == "sqs":
        if not settings.sync_queue_sqs_url:
            raise RuntimeError("SYNC_QUEUE_SQS_URL is required when SYNC_QUEUE_BACKEND=sqs")
        return SQSQueue(settings.sync_queue_sqs_url, settings.aws_region)
    return PostgresPollQueue()
