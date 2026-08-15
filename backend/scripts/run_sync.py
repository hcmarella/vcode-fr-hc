"""Manually trigger a sync from vcode-w-hc into the portal content store.

Usage:
    python scripts/run_sync.py --source ../vcode-w-hc [--ref main]
    python scripts/run_sync.py --source https://github.com/org/vcode-w-hc.git --ref main
"""
import argparse
import asyncio
from pathlib import Path

from app.config import get_settings
from app.db.base import async_session_factory
from app.sync_engine.runner import run_sync


async def main(source: str, ref: str | None) -> None:
    settings = get_settings()
    async with async_session_factory() as session:
        run = await run_sync(session, source, ref, Path(settings.sync_scratch_dir))
        print(f"Sync run {run.id}: {run.status.value}")
        print(f"Source commit: {run.source_commit_sha}")
        for content_type, counts in run.counts_json.items():
            print(f"  {content_type}: {counts}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Local path or git URL to vcode-w-hc")
    parser.add_argument("--ref", default=None, help="Branch/ref (git sources only)")
    args = parser.parse_args()
    asyncio.run(main(args.source, args.ref))
