from __future__ import annotations

import pytest

from matrix_codex.events import EVENT_TYPES, SCHEMA_VERSION, record, validate_event


def test_record_assigns_envelope_defaults() -> None:
    env = record("scan.completed", {"status": "healthy", "issue_count": 0}, repo="foo/bar")
    assert env.schema_version == SCHEMA_VERSION
    assert env.event_type == "scan.completed"
    assert env.repo == "foo/bar"
    assert env.event_id
    assert env.occurred_at


def test_validate_event_known_type_ok() -> None:
    env = record("repair.applied", {"engine": "selfrepair-safe", "applied": ["makefile"]})
    validate_event(env)  # must not raise


def test_validate_event_missing_required_field() -> None:
    env = record("scan.completed", {"status": "healthy"}, validate=False)
    with pytest.raises(Exception):
        validate_event(env)


def test_unknown_event_type_rejected() -> None:
    env = record("made.up.event", {"x": 1}, validate=False)
    with pytest.raises(ValueError):
        validate_event(env)


def test_record_with_validate_attaches_error_inline() -> None:
    env = record("scan.completed", {"status": "healthy"})  # missing issue_count
    assert "_validation_error" in env.payload


def test_every_event_type_has_schema() -> None:
    for ev_type, schema in EVENT_TYPES.items():
        assert schema["type"] == "object"
        assert "required" in schema or "properties" in schema, ev_type
