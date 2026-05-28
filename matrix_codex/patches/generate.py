"""Generate a patch from a working tree.

We shell out to ``git`` because the producer always runs in a context
with git available (either the controller host, the sandbox, or a CI
runner). No GitPython dependency for this -- the surface is too small.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from matrix_codex.patches.metadata import Patch


class GenerateError(RuntimeError):
    pass


def _run(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)
    if proc.returncode != 0:
        raise GenerateError(
            f"command failed: {' '.join(args)}\nstderr: {proc.stderr[:1000]}"
        )
    return proc.stdout


def diff_against_commit(
    repo_dir: Path,
    upstream_commit: str,
    *,
    paths: list[str] | None = None,
    binary: bool = True,
) -> bytes:
    """Return a unified diff of the current working tree vs ``upstream_commit``."""

    args = ["git", "diff", "--no-color", "--no-ext-diff"]
    if binary:
        args.append("--binary")
    args.extend([upstream_commit, "--"])
    if paths:
        args.extend(paths)
    text = _run(args, repo_dir)
    return text.encode("utf-8")


def format_patch_range(
    repo_dir: Path,
    from_ref: str,
    to_ref: str = "HEAD",
) -> bytes:
    """Return concatenated `git format-patch` output between two refs."""

    out = _run(
        ["git", "format-patch", "--stdout", f"{from_ref}..{to_ref}"],
        repo_dir,
    )
    return out.encode("utf-8")


def from_diff(
    body_bytes: bytes,
    *,
    upstream_repo: str,
    upstream_commit: str,
    target_commit: str | None = None,
    title: str | None = None,
    summary: str | None = None,
    mcp_manifest_id: str | None = None,
) -> Patch:
    return Patch.from_bytes(
        body_bytes,
        upstream_repo=upstream_repo,
        upstream_commit=upstream_commit,
        target_commit=target_commit,
        title=title,
        summary=summary,
        mcp_manifest_id=mcp_manifest_id,
        patch_format="git-format-patch",
    )
