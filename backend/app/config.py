from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://portal:portal@localhost:5432/portal"

    session_cookie_name: str = "portal_session"
    session_ttl_hours: int = 24 * 7

    sync_scratch_dir: str = "/var/lib/vcode-fr-hc/sync-scratch"
    default_source_path: str | None = None

    # --- Push sync (GitHub webhook) ---
    github_webhook_secret: str = ""
    # Repo the webhook is allowed to trigger syncs for, as GitHub's
    # `repository.full_name` (e.g. "hcmarella/vcode-w-hc"). Defense in depth
    # alongside the HMAC signature check -- the secret proves the request came
    # from GitHub, this makes sure it's *the right* GitHub repo/branch.
    sync_allowed_source_repo: str = ""
    sync_source_url: str = ""
    sync_source_ref: str = "main"

    # --- Sync queue backend ---
    # "postgres": worker polls sync_runs via SELECT ... FOR UPDATE SKIP LOCKED.
    #   No extra infra -- what docker-compose and local dev use.
    # "sqs": webhook enqueues to SQS, worker long-polls it. What EKS/prod uses
    #   -- see terraform/sqs.tf. Multiple worker replicas both backends
    #   support safely; SQS also survives a worker pod dying mid-poll without
    #   losing the pending job (visibility timeout requeues it).
    sync_queue_backend: str = "postgres"
    sync_queue_sqs_url: str | None = None
    aws_region: str = "us-east-1"
    sync_worker_poll_interval_seconds: float = 2.0

    anthropic_api_key: str = ""
    default_model: str = "claude-sonnet-5"

    pexels_api_key: str = ""

    docker_host: str | None = None
    sandbox_image: str = "vcode-fr-hc-sandbox:latest"
    sandbox_egress_network: str = "sandbox-egress"
    sandbox_internal_network: str = "sandbox-internal"

    session_idle_timeout_seconds: int = 900
    session_wall_clock_limit_seconds: int = 7200
    tool_command_timeout_seconds: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()
