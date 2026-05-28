"""Event envelope + per-type jsonschema registry."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

SCHEMA_VERSION = "events/v1"

logger = logging.getLogger(__name__)


class EventEnvelope(BaseModel):
    schema_version: str = SCHEMA_VERSION
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    occurred_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )
    repo: str | None = None
    run_id: str | None = None
    task_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


# Per-event jsonschema (just for the `payload` field).
# Keep tight; loosening can happen later without a schema bump.
EVENT_TYPES: dict[str, dict[str, Any]] = {
    "scan.completed": {
        "type": "object",
        "required": ["status", "issue_count"],
        "properties": {
            "status": {"enum": ["healthy", "degraded", "down", "unknown"]},
            "issue_count": {"type": "integer", "minimum": 0},
        },
        "additionalProperties": True,
    },
    "repair.applied": {
        "type": "object",
        "required": ["engine", "applied"],
        "properties": {
            "engine": {"enum": ["selfrepair-safe", "selfrepair-llm", "gitpilot"]},
            "applied": {"type": "array", "items": {"type": "string"}},
            "failed": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    },
    "repair.escalated": {
        "type": "object",
        "required": ["reason"],
        "properties": {"reason": {"type": "string"}},
        "additionalProperties": True,
    },
    "validate.completed": {
        "type": "object",
        "required": ["install_ok", "test_ok"],
        "properties": {
            "install_ok": {"type": "boolean"},
            "test_ok": {"type": "boolean"},
        },
        "additionalProperties": True,
    },
    "dispatch.requested": {
        "type": "object",
        "required": ["operation"],
        "properties": {"operation": {"type": "string"}},
        "additionalProperties": True,
    },
    "dispatch.failed": {
        "type": "object",
        "required": ["error"],
        "properties": {"error": {"type": "string"}},
        "additionalProperties": True,
    },
    "pr.opened": {
        "type": "object",
        "required": ["url"],
        "properties": {
            "url": {"type": "string", "format": "uri"},
            "risk_level": {"enum": ["low", "medium", "high", "critical"]},
        },
        "additionalProperties": True,
    },
    "mcp.imported": {
        "type": "object",
        "required": ["manifest_id"],
        "properties": {"manifest_id": {"type": "string"}},
        "additionalProperties": True,
    },
    "mcp.verified": {
        "type": "object",
        "required": ["manifest_id", "health"],
        "properties": {
            "manifest_id": {"type": "string"},
            "health": {"enum": ["verified", "broken", "unsupported", "unverified"]},
        },
        "additionalProperties": True,
    },
    "patch.stored": {
        "type": "object",
        "required": ["patch_id", "sha256", "backend"],
        "properties": {
            "patch_id": {"type": "string"},
            "sha256": {"type": "string"},
            "backend": {"type": "string"},
        },
        "additionalProperties": True,
    },
}


def validate_event(envelope: EventEnvelope) -> None:
    """Validate the payload against the per-type jsonschema. Raises on mismatch."""

    try:
        from jsonschema import validate
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("jsonschema is required for event validation") from exc
    schema = EVENT_TYPES.get(envelope.event_type)
    if schema is None:
        raise ValueError(f"unknown event_type: {envelope.event_type}")
    validate(instance=envelope.payload, schema=schema)


def record(
    event_type: str,
    payload: dict[str, Any],
    *,
    repo: str | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
    validate: bool = True,
) -> EventEnvelope:
    """Build an envelope and (optionally) validate it."""

    envelope = EventEnvelope(
        event_type=event_type,
        repo=repo,
        run_id=run_id,
        task_id=task_id,
        payload=payload,
    )
    if validate:
        try:
            validate_event(envelope)
        except Exception as exc:  # noqa: BLE001
            logger.warning("event_validation_failed: %s %s", event_type, exc)
            envelope.payload.setdefault("_validation_error", str(exc))
    return envelope
