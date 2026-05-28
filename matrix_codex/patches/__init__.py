"""Patch archive producer.

The producer pipeline:

1. ``generate`` -- diff the current sandbox tree against the upstream
   verified commit; emit a ``Patch`` record (metadata + body).
2. ``apply``    -- apply a previously-stored patch to a working tree,
   verifying the sha256 first.
3. ``store``    -- fan-out write: one authoritative backend, N mirrors.

The schema (`patches/v1`) is the contract for downstream consumers
(matrix-cli's `matrix install` flow). It is intentionally tiny: one
artifact is one record.
"""

from matrix_codex.patches.metadata import Patch, PatchBody, PatchMetadata, SCHEMA_VERSION, patch_id

__all__ = ["Patch", "PatchBody", "PatchMetadata", "SCHEMA_VERSION", "patch_id"]
