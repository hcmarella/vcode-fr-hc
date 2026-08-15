from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://portal:portal@localhost:5432/portal"

    session_cookie_name: str = "portal_session"
    session_ttl_hours: int = 24 * 7

    sync_scratch_dir: str = "/var/lib/vcode-fr-hc/sync-scratch"
    default_source_path: str | None = None

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
