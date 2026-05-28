from __future__ import annotations

from pathlib import Path

import pytest

from matrix_codex.patches.metadata import Patch
from matrix_codex.storage.patches_base import PatchStorageError
from matrix_codex.storage.patches_local import LocalPatchStorage


DIFF = b"diff --git a/foo b/foo\n@@ -1 +1 @@\n-old\n+new\n"


def _make_patch() -> Patch:
    return Patch.from_bytes(
        DIFF,
        upstream_repo="https://github.com/foo/bar",
        upstream_commit="c" * 40,
    )


def test_local_storage_put_get_roundtrip(tmp_path: Path) -> None:
    backend = LocalPatchStorage(tmp_path)
    patch = _make_patch()
    ref = backend.put(patch)
    assert Path(ref).is_file()
    assert backend.exists(patch.metadata.id)
    meta = backend.get_metadata(patch.metadata.id)
    body = backend.get_body(patch.metadata.id)
    assert meta.sha256 == patch.metadata.sha256
    assert body == DIFF


def test_local_storage_get_missing(tmp_path: Path) -> None:
    backend = LocalPatchStorage(tmp_path)
    with pytest.raises(PatchStorageError):
        backend.get_metadata("p-nope")


def test_local_storage_detects_tampered_body(tmp_path: Path) -> None:
    backend = LocalPatchStorage(tmp_path)
    patch = _make_patch()
    backend.put(patch)
    body_path = tmp_path / f"{patch.metadata.id}.patch"
    body_path.write_bytes(b"tampered")
    with pytest.raises(PatchStorageError):
        backend.get_body(patch.metadata.id)
