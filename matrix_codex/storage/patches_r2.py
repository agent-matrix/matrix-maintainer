"""Cloudflare R2 mirror for low-latency patch download.

Uses boto3 (S3-compatible) when installed.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from matrix_codex.patches.metadata import Patch, PatchMetadata
from matrix_codex.storage.patches_base import PatchStorage, PatchStorageError

logger = logging.getLogger(__name__)


class R2PatchStorage(PatchStorage):
    name = "r2"

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
    ) -> None:
        try:
            import boto3  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise PatchStorageError(
                "boto3 is not installed; `pip install matrix-maintainer[mcp]`"
            ) from exc
        self._bucket = bucket
        self._endpoint = endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key

    def _client(self) -> Any:  # pragma: no cover - network
        import boto3
        from botocore.config import Config

        return boto3.client(
            "s3",
            endpoint_url=self._endpoint,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            config=Config(signature_version="s3v4"),
        )

    def put(self, patch: Patch) -> str:  # pragma: no cover - network
        client = self._client()
        meta = json.dumps(patch.metadata.model_dump(mode="json"), indent=2).encode("utf-8")
        body = patch.body.to_bytes()
        client.put_object(
            Bucket=self._bucket,
            Key=f"patches/{patch.metadata.id}.json",
            Body=meta,
            ContentType="application/json",
        )
        client.put_object(
            Bucket=self._bucket,
            Key=f"patches/{patch.metadata.id}.patch",
            Body=body,
            ContentType="text/x-diff",
        )
        return f"{self._endpoint}/{self._bucket}/patches/{patch.metadata.id}.patch"

    def get_metadata(self, patch_id: str) -> PatchMetadata:  # pragma: no cover - network
        client = self._client()
        obj = client.get_object(Bucket=self._bucket, Key=f"patches/{patch_id}.json")
        data = obj["Body"].read()
        return PatchMetadata.model_validate(json.loads(data.decode("utf-8")))

    def get_body(self, patch_id: str) -> bytes:  # pragma: no cover - network
        client = self._client()
        obj = client.get_object(Bucket=self._bucket, Key=f"patches/{patch_id}.patch")
        return obj["Body"].read()

    def exists(self, patch_id: str) -> bool:  # pragma: no cover - network
        try:
            self.get_metadata(patch_id)
            return True
        except Exception:
            return False
