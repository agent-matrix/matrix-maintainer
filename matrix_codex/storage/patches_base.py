"""Storage adapter Protocol for patch artifacts.

A backend stores two things keyed by ``patch.metadata.id``:

* the metadata JSON
* the patch body bytes (verified by sha256 on read)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from matrix_codex.patches.metadata import Patch, PatchMetadata


class PatchStorageError(RuntimeError):
    pass


@runtime_checkable
class PatchStorage(Protocol):
    name: str

    def put(self, patch: Patch) -> str:
        """Persist patch; return a backend-specific reference (URL or path)."""

    def get_metadata(self, patch_id: str) -> PatchMetadata: ...

    def get_body(self, patch_id: str) -> bytes: ...

    def exists(self, patch_id: str) -> bool: ...
