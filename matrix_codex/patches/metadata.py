"""Patch record schema (`patches/v1`).

A patch is identified by the sha256 of its body. URLs rot, digests
don't. Manifests reference patches by `id`, never by URL.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl

SCHEMA_VERSION = "patches/v1"

PatchFormat = Literal["git-format-patch", "unified"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_id(sha256: str) -> str:
    """Stable id: first 16 hex chars of the sha256. Collision-safe for
    realistic patch volumes."""

    return f"p-{sha256[:16]}"


class PatchMetadata(BaseModel):
    schema_version: str = SCHEMA_VERSION
    id: str  # `p-<sha256-16>`
    sha256: str  # full hex digest of the patch body bytes
    size_bytes: int
    patch_format: PatchFormat = "git-format-patch"
    upstream_repo: HttpUrl
    upstream_commit: str  # full sha of the upstream commit the patch applies on top of
    target_commit: str | None = None  # what the patch produces, if known
    title: str | None = None
    summary: str | None = None
    mcp_manifest_id: str | None = None
    tool_version: str = "matrix-maintainer/0.2"
    sigstore_signature: str | None = None
    sigstore_certificate: str | None = None
    created_at: str = Field(default_factory=_utc_now)
    extra: dict[str, Any] = Field(default_factory=dict)

    def verify(self, body: bytes) -> bool:
        return sha256_hex(body) == self.sha256


class PatchBody(BaseModel):
    """In-memory wrapper for the patch bytes."""

    schema_version: str = SCHEMA_VERSION
    encoding: Literal["text/utf-8", "binary/base64"] = "text/utf-8"
    content: str  # utf-8 patch text OR base64 for binary

    def to_bytes(self) -> bytes:
        if self.encoding == "text/utf-8":
            return self.content.encode("utf-8")
        import base64

        return base64.b64decode(self.content)


class Patch(BaseModel):
    """Metadata + body together. Most APIs return only metadata; the body
    is fetched separately by digest."""

    metadata: PatchMetadata
    body: PatchBody

    @classmethod
    def from_bytes(
        cls,
        body_bytes: bytes,
        *,
        upstream_repo: str,
        upstream_commit: str,
        title: str | None = None,
        summary: str | None = None,
        mcp_manifest_id: str | None = None,
        patch_format: PatchFormat = "git-format-patch",
        target_commit: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> "Patch":
        try:
            text = body_bytes.decode("utf-8")
            encoding: Literal["text/utf-8", "binary/base64"] = "text/utf-8"
            content = text
        except UnicodeDecodeError:
            import base64

            encoding = "binary/base64"
            content = base64.b64encode(body_bytes).decode("ascii")
        sha = sha256_hex(body_bytes)
        metadata = PatchMetadata(
            id=patch_id(sha),
            sha256=sha,
            size_bytes=len(body_bytes),
            patch_format=patch_format,
            upstream_repo=upstream_repo,
            upstream_commit=upstream_commit,
            target_commit=target_commit,
            title=title,
            summary=summary,
            mcp_manifest_id=mcp_manifest_id,
            extra=extra or {},
        )
        return cls(metadata=metadata, body=PatchBody(encoding=encoding, content=content))
