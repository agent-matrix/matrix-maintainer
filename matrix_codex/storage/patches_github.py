"""GitHub-backed patch storage (authoritative in production).

Layout in the target repo (default `agent-matrix/mcp-patches`):

    patches/<patch_id>.json   -- metadata
    patches/<patch_id>.patch  -- body

Writes use the GitHub Contents API (no clone needed). Reads use raw
githubusercontent for the body (cheap) and the Contents API for the
metadata (for the sha verification).
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import httpx

from matrix_codex.patches.metadata import Patch, PatchMetadata
from matrix_codex.storage.patches_base import PatchStorage, PatchStorageError

logger = logging.getLogger(__name__)


class GitHubPatchStorage(PatchStorage):
    name = "github"

    def __init__(
        self,
        *,
        repo: str,
        branch: str = "main",
        token: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not token:
            raise PatchStorageError("GitHubPatchStorage requires a token")
        self._repo = repo
        self._branch = branch
        self._token = token
        self._client = http_client or httpx.Client(timeout=httpx.Timeout(60.0))

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _api(self, path: str) -> str:
        return f"https://api.github.com/repos/{self._repo}/contents/{path}"

    def _raw(self, path: str) -> str:
        return f"https://raw.githubusercontent.com/{self._repo}/{self._branch}/{path}"

    def _get_sha(self, path: str) -> str | None:
        resp = self._client.get(self._api(path), headers=self._headers(), params={"ref": self._branch})
        if resp.status_code == 200:
            return resp.json().get("sha")
        if resp.status_code == 404:
            return None
        raise PatchStorageError(f"github sha lookup failed: {resp.status_code} {resp.text[:200]}")

    def _put(self, path: str, content_bytes: bytes, message: str) -> dict[str, Any]:
        sha = self._get_sha(path)
        body: dict[str, Any] = {
            "message": message,
            "branch": self._branch,
            "content": base64.b64encode(content_bytes).decode("ascii"),
        }
        if sha:
            body["sha"] = sha
        resp = self._client.put(self._api(path), headers=self._headers(), json=body)
        if resp.status_code not in (200, 201):
            raise PatchStorageError(
                f"github put failed: {resp.status_code} {resp.text[:500]}"
            )
        return resp.json()

    def put(self, patch: Patch) -> str:
        meta_path = f"patches/{patch.metadata.id}.json"
        body_path = f"patches/{patch.metadata.id}.patch"
        meta_bytes = json.dumps(patch.metadata.model_dump(mode="json"), indent=2).encode("utf-8")
        body_bytes = patch.body.to_bytes()

        self._put(meta_path, meta_bytes, f"patches: add metadata for {patch.metadata.id}")
        self._put(body_path, body_bytes, f"patches: add body for {patch.metadata.id}")
        return self._raw(body_path)

    def get_metadata(self, patch_id: str) -> PatchMetadata:
        resp = self._client.get(self._raw(f"patches/{patch_id}.json"), timeout=30.0)
        if resp.status_code == 404:
            raise PatchStorageError(f"patch metadata not found: {patch_id}")
        resp.raise_for_status()
        return PatchMetadata.model_validate(resp.json())

    def get_body(self, patch_id: str) -> bytes:
        meta = self.get_metadata(patch_id)
        resp = self._client.get(self._raw(f"patches/{patch_id}.patch"), timeout=60.0)
        if resp.status_code == 404:
            raise PatchStorageError(f"patch body not found: {patch_id}")
        resp.raise_for_status()
        data = resp.content
        if not meta.verify(data):
            raise PatchStorageError(f"sha256 mismatch on {patch_id}")
        return data

    def exists(self, patch_id: str) -> bool:
        return self._get_sha(f"patches/{patch_id}.json") is not None
