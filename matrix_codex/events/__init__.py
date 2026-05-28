"""Versioned event registry.

Producers go through :func:`record`. Consumers (status site, badge
publisher, audit log replay) load events from JSON and validate via
:func:`validate_event`.

The schema id is `events/v1`. Forward-compatibility rules match the
rest of the ecosystem: additive fields free, removed/renamed fields
require a new schema version.
"""

from matrix_codex.events.schema import EVENT_TYPES, EventEnvelope, SCHEMA_VERSION, record, validate_event

__all__ = ["EVENT_TYPES", "EventEnvelope", "SCHEMA_VERSION", "record", "validate_event"]
