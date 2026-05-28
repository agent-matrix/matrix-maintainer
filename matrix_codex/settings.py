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
    worker_workflow_file: str = Field(default="matrix-maintainer.yml", alias="WORKER_WORKFLOW_FILE")

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
    gitpilot_mode: str = Field(default="auto", alias="GITPILOT_MODE")
    gitpilot_provider: str = Field(default="openai", alias="GITPILOT_PROVIDER")

    matrixlab_bin: str = Field(default="matrixlab", alias="MATRIXLAB_BIN")
    matrixlab_enabled: bool = Field(default=True, alias="MATRIXLAB_ENABLED")
    matrixlab_fallback_local: bool = Field(default=True, alias="MATRIXLAB_FALLBACK_LOCAL")

    matrix_ai_endpoint: str = Field(default="http://matrix-ai.internal/plan", alias="MATRIX_AI_ENDPOINT")
    matrix_guardian_endpoint: str = Field(default="http://matrix-guardian.internal/approve", alias="MATRIX_GUARDIAN_ENDPOINT")
    matrix_treasury_endpoint: str = Field(default="http://matrix-treasury.internal/budget", alias="MATRIX_TREASURY_ENDPOINT")
    matrix_hub_endpoint: str = Field(default="http://matrix-hub.internal/events", alias="MATRIX_HUB_ENDPOINT")
    persistence_db_url: str = Field(default="sqlite:///state/matrix_maintainer.db", alias="PERSISTENCE_DB_URL")
    scan_schedule_cron: str = Field(default="0 3 * * *", alias="SCAN_SCHEDULE_CRON")

    site_base_url: str | None = Field(default=None, alias="SITE_BASE_URL")
    site_title: str = Field(default="Matrix Maintainer", alias="SITE_TITLE")
    site_description: str = Field(
        default="Orchestration control plane for repository and MCP-server maintenance across the Agent-Matrix ecosystem.",
        alias="SITE_DESCRIPTION",
    )

    allow_autofix_pr: bool = Field(default=True, alias="ALLOW_AUTOFIX_PR")
    allow_direct_push: bool = Field(default=False, alias="ALLOW_DIRECT_PUSH")
    max_autofix_files: int = Field(default=10, alias="MAX_AUTOFIX_FILES")

    # --- SelfRepair adapter (Phase 1) --------------------------------------
    selfrepair_mode: str = Field(default="auto", alias="SELFREPAIR_MODE")
    selfrepair_base_url: str | None = Field(default=None, alias="SELFREPAIR_BASE_URL")
    selfrepair_api_key: str | None = Field(default=None, alias="SELFREPAIR_API_KEY")
    selfrepair_timeout_seconds: float = Field(default=120.0, alias="SELFREPAIR_TIMEOUT_SECONDS")

    # --- OllaBridge Cloud (the single LLM gateway) -------------------------
    # All LLM calls -- planner, GitPilot, ad-hoc completions -- route here.
    # The API key is named after the workspace, e.g. "Matrix-Maintainer".
    ollabridge_base_url: str = Field(default="https://api.ollabridge.com/v1", alias="OLLABRIDGE_BASE_URL")
    ollabridge_api_key: str | None = Field(default=None, alias="OLLABRIDGE_API_KEY")
    ollabridge_model: str = Field(default="qwen2.5:7b", alias="OLLABRIDGE_MODEL")
    ollabridge_timeout_seconds: float = Field(default=120.0, alias="OLLABRIDGE_TIMEOUT_SECONDS")
    ollabridge_organization: str | None = Field(default=None, alias="OLLABRIDGE_ORGANIZATION")

    # --- MCP server maintenance (Phase 3) ----------------------------------
    mcp_state_dir: Path = Field(default=Path("state/mcp"), alias="MCP_STATE_DIR")
    mcp_default_runtime: str = Field(default="python", alias="MCP_DEFAULT_RUNTIME")

    # --- Patch archive (Phase 4) -------------------------------------------
    patches_state_dir: Path = Field(default=Path("state/patches"), alias="PATCHES_STATE_DIR")
    patches_github_repo: str = Field(default="agent-matrix/mcp-patches", alias="PATCHES_GITHUB_REPO")
    patches_github_branch: str = Field(default="main", alias="PATCHES_GITHUB_BRANCH")
    patches_hf_repo: str | None = Field(default=None, alias="PATCHES_HF_REPO")
    patches_hf_token: str | None = Field(default=None, alias="PATCHES_HF_TOKEN")
    patches_r2_bucket: str | None = Field(default=None, alias="PATCHES_R2_BUCKET")
    patches_r2_endpoint: str | None = Field(default=None, alias="PATCHES_R2_ENDPOINT")
    patches_r2_access_key: str | None = Field(default=None, alias="PATCHES_R2_ACCESS_KEY")
    patches_r2_secret_key: str | None = Field(default=None, alias="PATCHES_R2_SECRET_KEY")

    def ensure_directories(self) -> None:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.status_site_dir.mkdir(parents=True, exist_ok=True)
        (self.status_site_dir / "data").mkdir(parents=True, exist_ok=True)
        self.mcp_state_dir.mkdir(parents=True, exist_ok=True)
        self.patches_state_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
