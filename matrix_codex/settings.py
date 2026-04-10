from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    cross_repo_token: str | None = Field(default=None, alias="CROSS_REPO_TOKEN")
    github_org: str = Field(default="agent-matrix", alias="GITHUB_ORG")
    github_base_branch: str = Field(default="main", alias="GITHUB_BASE_BRANCH")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    work_dir: Path = Field(default=Path("work"), alias="WORK_DIR")
    state_dir: Path = Field(default=Path("state"), alias="STATE_DIR")
    status_site_dir: Path = Field(default=Path("status-site"), alias="STATUS_SITE_DIR")

    max_fix_attempts: int = Field(default=3, alias="MAX_FIX_ATTEMPTS")
    repo_timeout_seconds: int = Field(default=900, alias="REPO_TIMEOUT_SECONDS")
    start_timeout_seconds: int = Field(default=60, alias="START_TIMEOUT_SECONDS")

    gitpilot_bin: str = Field(default="gitpilot", alias="GITPILOT_BIN")
    gitpilot_enabled: bool = Field(default=True, alias="GITPILOT_ENABLED")
    gitpilot_message_model: str | None = Field(default=None, alias="GITPILOT_MESSAGE_MODEL")

    matrixlab_bin: str = Field(default="matrixlab", alias="MATRIXLAB_BIN")
    matrixlab_enabled: bool = Field(default=True, alias="MATRIXLAB_ENABLED")
    matrixlab_fallback_local: bool = Field(default=True, alias="MATRIXLAB_FALLBACK_LOCAL")

    site_base_url: str | None = Field(default=None, alias="SITE_BASE_URL")
    site_title: str = Field(default="Matrix Codex", alias="SITE_TITLE")
    site_description: str = Field(default="Controller dashboard for Matrix Codex orchestration and repository health.", alias="SITE_DESCRIPTION")

    allow_autofix_pr: bool = Field(default=True, alias="ALLOW_AUTOFIX_PR")
    allow_direct_push: bool = Field(default=False, alias="ALLOW_DIRECT_PUSH")
    max_autofix_files: int = Field(default=10, alias="MAX_AUTOFIX_FILES")

    def ensure_directories(self) -> None:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.status_site_dir.mkdir(parents=True, exist_ok=True)
        (self.status_site_dir / "data").mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings

