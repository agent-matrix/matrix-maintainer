"""Apply a previously-stored patch to a working tree.

The contract:

1. Caller fetches ``PatchMetadata`` and the body bytes via the storage
   adapter.
2. Caller calls :func:`verify_and_apply`, which sha256-checks the body
   BEFORE letting git touch the working tree.
3. On a sha256 mismatch we raise; we NEVER apply an unverified patch.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from matrix_codex.patches.metadata import PatchMetadata, sha256_hex


class PatchVerifyError(RuntimeError):
    pass


class PatchApplyError(RuntimeError):
    pass


def verify(metadata: PatchMetadata, body: bytes) -> None:
    actual = sha256_hex(body)
    if actual != metadata.sha256:
        raise PatchVerifyError(
            f"sha256 mismatch: expected {metadata.sha256} got {actual}"
        )


def apply(
    repo_dir: Path,
    metadata: PatchMetadata,
    body: bytes,
    *,
    check_only: bool = False,
) -> None:
    """Verify and apply ``body`` to ``repo_dir``."""

    verify(metadata, body)
    args = ["git", "apply", "--whitespace=nowarn"]
    if check_only:
        args.append("--check")
    proc = subprocess.run(
        args,
        cwd=str(repo_dir),
        input=body,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise PatchApplyError(
            f"git apply failed: rc={proc.returncode} stderr={proc.stderr.decode('utf-8', 'replace')[:1000]}"
        )


def verify_and_apply(
    repo_dir: Path,
    metadata: PatchMetadata,
    body: bytes,
) -> None:
    apply(repo_dir, metadata, body)
