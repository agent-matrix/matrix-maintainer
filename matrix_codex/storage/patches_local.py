"""Filesystem patch storage. Authoritative in dev / CI; mirror in prod."""

from __future__ import annotations

import json
from pathlib import Path

from matrix_codex.patches.metadata import Patch, PatchBody, PatchMetadata
from matrix_codex.storage.patches_base import PatchStorage, PatchStorageError


class LocalPatchStorage(PatchStorage):
    name = "local"

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _meta_path(self, patch_id: str) -> Path:
        return self._root / f"{patch_id}.json"

    def _body_path(self, patch_id: str) -> Path:
        return self._root / f"{patch_id}.patch"

    def put(self, patch: Patch) -> str:
        meta = self._meta_path(patch.metadata.id)
        body = self._body_path(patch.metadata.id)
        meta.write_text(json.dumps(patch.metadata.model_dump(mode="json"), indent=2), encoding="utf-8")
        body.write_bytes(patch.body.to_bytes())
        return str(meta)

    def get_metadata(self, patch_id: str) -> PatchMetadata:
        path = self._meta_path(patch_id)
        if not path.is_file():
            raise PatchStorageError(f"no metadata at {path}")
        return PatchMetadata.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def get_body(self, patch_id: str) -> bytes:
        path = self._body_path(patch_id)
        if not path.is_file():
            raise PatchStorageError(f"no body at {path}")
        data = path.read_bytes()
        meta = self.get_metadata(patch_id)
        if not meta.verify(data):
            raise PatchStorageError(f"sha256 mismatch on {patch_id}")
        return data

    def exists(self, patch_id: str) -> bool:
        return self._meta_path(patch_id).is_file() and self._body_path(patch_id).is_file()
