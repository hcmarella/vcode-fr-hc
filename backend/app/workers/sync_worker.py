"""Background worker that executes queued syncs. Runs as a separate process
(and, in Docker/k8s, a separate container/pod) from the API server -- see
docker-compose.yml's `worker` service and k8s/deployment-worker.yaml.

Horizontally scalable by design: run N replicas and they safely divide up
work, whichever queue backend is configured (see app/sync_engine/queue.py).
That's the piece that makes "more teams pushing at the same time" a
throughput knob (add replicas) instead of a correctness problem.

Usage:
    python -m app.workers.sync_worker
"""

import asyncio
import logging
import signal
from pathlib import Path

from app.config import get_settings
from app.db.base import async_session_factory
from app.sync_engine.runner import claim_next_pending, execute_run

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_shutdown = asyncio.Event()


def _handle_signal(*_args) -> None:
    logger.info("Shutdown signal received, finishing current job then exiting")
    _shutdown.set()


async def _run_one_postgres(scratch_dir: Path) -> bool:
    """Claim and execute a single pending run. Returns True if one was found."""
    async with async_session_factory() as session:
        run = await claim_next_pending(session)
        if run is None:
            return False
        logger.info("Claimed sync run %s (source=%s ref=%s)", run.id, run.source, run.ref)
        try:
            await execute_run(session, run, scratch_dir)
            logger.info("Sync run %s completed: %s", run.id, run.status.value)
        except Exception:
            logger.exception("Sync run %s failed", run.id)
        return True


async def _run_one_sqs(scratch_dir: Path, queue_url: str, region: str) -> bool:
    import uuid

    import boto3

    from app.db.models.sync import SyncRun, SyncRunStatus
    from app.sync_engine.runner import claim_run

    client = boto3.client("sqs", region_name=region)
    resp = await asyncio.to_thread(
        client.receive_message,
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10,  # long poll -- avoids busy-looping SQS ReceiveMessage calls
    )
    messages = resp.get("Messages", [])
    if not messages:
        return False

    message = messages[0]
    run_id = uuid.UUID(message["Body"])

    async with async_session_factory() as session:
        run = await session.get(SyncRun, run_id)
        if run is None or run.status != SyncRunStatus.PENDING:
            # Already claimed/handled (e.g. by another worker replica, or a
            # redelivered message after a prior success). Delete and move on
            # -- SQS's at-least-once delivery makes this a normal occurrence,
            # not a bug.
            await asyncio.to_thread(
                client.delete_message, QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]
            )
            return True

        logger.info("Claimed sync run %s via SQS (source=%s ref=%s)", run.id, run.source, run.ref)
        await claim_run(session, run)
        try:
            await execute_run(session, run, scratch_dir)
            logger.info("Sync run %s completed: %s", run.id, run.status.value)
            await asyncio.to_thread(
                client.delete_message, QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]
            )
        except Exception:
            logger.exception("Sync run %s failed, leaving message for SQS retry", run.id)
            # Don't delete -- the message becomes visible again after the
            # queue's visibility timeout and another worker will retry it.
        return True


async def run_forever() -> None:
    settings = get_settings()
    scratch_dir = Path(settings.sync_scratch_dir)
    backend = settings.sync_queue_backend
    logger.info("Sync worker starting (queue backend=%s)", backend)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_signal)

    while not _shutdown.is_set():
        try:
            if backend == "sqs":
                found = await _run_one_sqs(
                    scratch_dir, settings.sync_queue_sqs_url, settings.aws_region
                )
            else:
                found = await _run_one_postgres(scratch_dir)
        except Exception:
            logger.exception("Worker loop iteration failed")
            found = False

        if not found:
            try:
                await asyncio.wait_for(
                    _shutdown.wait(), timeout=settings.sync_worker_poll_interval_seconds
                )
            except asyncio.TimeoutError:
                pass  # normal poll-interval tick, not a shutdown

    logger.info("Sync worker exiting")


if __name__ == "__main__":
    asyncio.run(run_forever())
