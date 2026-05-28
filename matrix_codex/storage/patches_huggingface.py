"""Hugging Face dataset mirror for patches.

Uses huggingface_hub when installed; raises ``PatchStorageError`` with
an explanatory message otherwise. We intentionally don't hard-depend on
huggingface_hub -- it's only needed when an operator opts into the HF
mirror via ``PATCHES_HF_REPO``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from matrix_codex.patches.metadata import Patch, PatchMetadata
from matrix_codex.storage.patches_base import PatchStorage, PatchStorageError

logger = logging.getLogger(__name__)


class HuggingFacePatchStorage(PatchStorage):
    name = "huggingface"

    def __init__(self, *, repo_id: str, token: str | None = None) -> None:
        try:
            from huggingface_hub import HfApi  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise PatchStorageError(
                "huggingface_hub is not installed; `pip install matrix-maintainer[mcp]`"
            ) from exc
        if not token:
            raise PatchStorageError("HuggingFacePatchStorage requires PATCHES_HF_TOKEN")
        self._repo_id = repo_id
        self._token = token

    def _api(self):  # pragma: no cover - thin wrapper
        from huggingface_hub import HfApi

        return HfApi(token=self._token)

    def put(self, patch: Patch) -> str:  # pragma: no cover - network
        with TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            meta_path = tmp_dir / f"{patch.metadata.id}.json"
            body_path = tmp_dir / f"{patch.metadata.id}.patch"
            meta_path.write_text(
                json.dumps(patch.metadata.model_dump(mode="json"), indent=2),
                encoding="utf-8",
            )
            body_path.write_bytes(patch.body.to_bytes())
            api = self._api()
            api.upload_file(
                path_or_fileobj=str(meta_path),
                path_in_repo=f"patches/{patch.metadata.id}.json",
                repo_id=self._repo_id,
                repo_type="dataset",
                commit_message=f"patches: add {patch.metadata.id}",
            )
            api.upload_file(
                path_or_fileobj=str(body_path),
                path_in_repo=f"patches/{patch.metadata.id}.patch",
                repo_id=self._repo_id,
                repo_type="dataset",
                commit_message=f"patches: add body {patch.metadata.id}",
            )
            return f"https://huggingface.co/datasets/{self._repo_id}/blob/main/patches/{patch.metadata.id}.patch"

    def get_metadata(self, patch_id: str) -> PatchMetadata:  # pragma: no cover - network
        from huggingface_hub import hf_hub_download

        path = hf_hub_download(
            repo_id=self._repo_id,
            filename=f"patches/{patch_id}.json",
            repo_type="dataset",
            token=self._token,
        )
        return PatchMetadata.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))

    def get_body(self, patch_id: str) -> bytes:  # pragma: no cover - network
        from huggingface_hub import hf_hub_download

        path = hf_hub_download(
            repo_id=self._repo_id,
            filename=f"patches/{patch_id}.patch",
            repo_type="dataset",
            token=self._token,
        )
        return Path(path).read_bytes()

    def exists(self, patch_id: str) -> bool:  # pragma: no cover - network
        try:
            self.get_metadata(patch_id)
            return True
        except Exception:
            return False
