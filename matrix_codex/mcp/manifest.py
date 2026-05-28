"""Wire-stable MCP manifest schema.

Versioned with ``schema_version = "mcp/v1"``. Backward-compatibility
rules (additive fields only without a version bump) match the rest of
the ecosystem -- see ``docs/design/selfrepair-client-contract.md``
section "Compatibility rules".
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

SCHEMA_VERSION = "mcp/v1"

RiskTag = Literal[
    "network-access",
    "filesystem-access",
    "secrets-required",
    "executes-code",
    "persistent-state",
    "third-party-api",
]

RuntimeTag = Literal["python", "node", "go", "rust", "docker", "jvm", "shell", "other"]

QualityTag = Literal[
    "has-tests",
    "has-ci",
    "has-readme",
    "has-license",
    "has-typing",
    "agent-matrix-verified",
]

MaintenanceTag = Literal[
    "selfrepair-scanned",
    "gitpilot-reviewed",
    "patch-available",
    "upstream-active",
    "upstream-abandoned",
]

HealthStatus = Literal["unverified", "verifying", "verified", "broken", "unsupported"]


def _utc_now_str() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class MCPSource(BaseModel):
    repo: HttpUrl
    commit: str | None = None
    tag: str | None = None
    license_id: str | None = None
    license_url: HttpUrl | None = None


class MCPTags(BaseModel):
    capability: list[str] = Field(default_factory=list)
    runtime: list[RuntimeTag] = Field(default_factory=list)
    risk: list[RiskTag] = Field(default_factory=list)
    quality: list[QualityTag] = Field(default_factory=list)
    maintenance: list[MaintenanceTag] = Field(default_factory=list)


class MCPStatus(BaseModel):
    health: HealthStatus = "unverified"
    latest_verified_commit: str | None = None
    latest_verified_at: str | None = None
    notes: list[str] = Field(default_factory=list)


class MCPManifest(BaseModel):
    """Top-level manifest record stored in ``state/mcp/<id>.json``."""

    schema_version: str = SCHEMA_VERSION
    id: str
    type: Literal["mcp-server"] = "mcp-server"
    title: str | None = None
    summary: str | None = None
    source: MCPSource
    tags: MCPTags = Field(default_factory=MCPTags)
    status: MCPStatus = Field(default_factory=MCPStatus)
    generated_at: str = Field(default_factory=_utc_now_str)
    updated_at: str = Field(default_factory=_utc_now_str)
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def _id_slug(cls, value: str) -> str:
        if not value or any(c.isspace() for c in value):
            raise ValueError("manifest id must be a non-empty slug without whitespace")
        return value.lower()

    def touch(self) -> None:
        self.updated_at = _utc_now_str()
