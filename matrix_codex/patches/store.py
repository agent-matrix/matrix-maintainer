"""Multi-backend writer with one authoritative backend + N mirrors.

Authoritative MUST succeed. Mirrors may fail without aborting; failures
are returned in the result so the caller can decide what to do.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from matrix_codex.patches.metadata import Patch
from matrix_codex.settings import Settings, get_settings
from matrix_codex.storage.patches_base import PatchStorage, PatchStorageError
from matrix_codex.storage.patches_github import GitHubPatchStorage
from matrix_codex.storage.patches_huggingface import HuggingFacePatchStorage
from matrix_codex.storage.patches_local import LocalPatchStorage
from matrix_codex.storage.patches_r2 import R2PatchStorage

logger = logging.getLogger(__name__)


@dataclass
class StoreResult:
    authoritative_backend: str
    authoritative_ref: str
    mirror_refs: dict[str, str]
    mirror_errors: dict[str, str]


_BACKEND_NAMES = ("local", "github", "huggingface", "r2")


def _make_backend(name: str, settings: Settings) -> PatchStorage:
    if name == "local":
        return LocalPatchStorage(settings.patches_state_dir)
    if name == "github":
        token = settings.cross_repo_token or settings.github_token
        return GitHubPatchStorage(
            repo=settings.patches_github_repo,
            branch=settings.patches_github_branch,
            token=token,
        )
    if name == "huggingface":
        if not settings.patches_hf_repo:
            raise PatchStorageError("PATCHES_HF_REPO not set")
        return HuggingFacePatchStorage(
            repo_id=settings.patches_hf_repo,
            token=settings.patches_hf_token,
        )
    if name == "r2":
        if not (settings.patches_r2_bucket and settings.patches_r2_endpoint):
            raise PatchStorageError("PATCHES_R2_* not fully configured")
        return R2PatchStorage(
            bucket=settings.patches_r2_bucket,
            endpoint_url=settings.patches_r2_endpoint,
            access_key=settings.patches_r2_access_key or "",
            secret_key=settings.patches_r2_secret_key or "",
        )
    raise PatchStorageError(f"unknown backend: {name}")


def store(
    patch: Patch,
    *,
    authoritative: str = "github",
    mirrors: tuple[str, ...] = (),
    settings: Settings | None = None,
) -> StoreResult:
    """Write a patch to the authoritative backend and zero or more mirrors."""

    s = settings or get_settings()
    if authoritative not in _BACKEND_NAMES:
        raise PatchStorageError(f"unknown authoritative backend: {authoritative}")
    for m in mirrors:
        if m not in _BACKEND_NAMES:
            raise PatchStorageError(f"unknown mirror backend: {m}")

    auth_backend = _make_backend(authoritative, s)
    auth_ref = auth_backend.put(patch)

    mirror_refs: dict[str, str] = {}
    mirror_errors: dict[str, str] = {}
    for name in mirrors:
        if name == authoritative:
            continue
        try:
            backend = _make_backend(name, s)
            mirror_refs[name] = backend.put(patch)
        except Exception as exc:  # noqa: BLE001 - mirror failures must not abort
            logger.warning("patch_mirror_failed: %s -> %s", name, exc)
            mirror_errors[name] = str(exc)

    return StoreResult(
        authoritative_backend=authoritative,
        authoritative_ref=auth_ref,
        mirror_refs=mirror_refs,
        mirror_errors=mirror_errors,
    )
