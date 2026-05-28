"""Wire-stable DTOs for the SelfRepair client contract.

These models are deliberately separate from :mod:`matrix_codex.models`:

* They carry an explicit ``schema_version`` so the contract can evolve
  without breaking older HTTP peers.
* They are the *only* shapes that cross the SelfRepair boundary --
  internal Matrix Codex models are mapped to/from these by adapters.

Do not import these from anywhere except :mod:`matrix_codex.selfrepair`
implementations and the call sites that depend on the boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION = "selfrepair/v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


Severity = Literal["low", "medium", "high", "critical"]
Status = Literal["healthy", "degraded", "down", "unknown"]


class RepoRefDTO(BaseModel):
    """Identifier for a repository the client should operate on."""

    schema_version: str = SCHEMA_VERSION
    full_name: str
    clone_url: str
    default_branch: str = "main"
    platform: Literal["github", "gitlab", "huggingface"] = "github"
    private: bool = False


class HealthIssueDTO(BaseModel):
    schema_version: str = SCHEMA_VERSION
    repo: str
    issue_type: str
    details: str = ""
    severity: Severity = "medium"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepoHealthReportDTO(BaseModel):
    schema_version: str = SCHEMA_VERSION
    repo: RepoRefDTO
    generated_at: str = Field(default_factory=_utc_now)
    status: Status = "unknown"
    issues: list[HealthIssueDTO] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepairResultDTO(BaseModel):
    schema_version: str = SCHEMA_VERSION
    repo: str
    applied: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    branch: str | None = None
    needs_escalation: bool = False
    escalation_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationReportDTO(BaseModel):
    schema_version: str = SCHEMA_VERSION
    repo: str
    install_ok: bool = False
    test_ok: bool = False
    start_ok: bool = False
    health_test_ok: bool = False
    sandbox: Literal["matrixlab", "local", "none"] = "none"
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def ok(self) -> bool:  # pragma: no cover - convenience
        return self.install_ok and self.test_ok and self.health_test_ok


class JsonReportDTO(BaseModel):
    """Aggregate report suitable for attaching to a PR or storing."""

    schema_version: str = SCHEMA_VERSION
    repo: str
    generated_at: str = Field(default_factory=_utc_now)
    health: RepoHealthReportDTO | None = None
    repair: RepairResultDTO | None = None
    validation: ValidationReportDTO | None = None
    audit: dict[str, Any] = Field(default_factory=dict)
