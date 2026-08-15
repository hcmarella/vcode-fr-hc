import uuid
from datetime import datetime

from pydantic import BaseModel

from app.db.models.sync import SyncContentType, SyncFlagType, SyncRunStatus


class SyncRunRequest(BaseModel):
    source: str
    ref: str | None = None


class SyncRunResponse(BaseModel):
    id: uuid.UUID
    started_at: datetime
    finished_at: datetime | None
    status: SyncRunStatus
    source_ref: str
    source_commit_sha: str | None
    counts_json: dict
    error_message: str | None

    model_config = {"from_attributes": True}


class SyncRunFlagResponse(BaseModel):
    id: uuid.UUID
    sync_run_id: uuid.UUID
    flag_type: SyncFlagType
    source_path: str
    content_type: SyncContentType
    details_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}
