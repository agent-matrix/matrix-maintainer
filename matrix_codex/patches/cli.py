"""`matrix-maintainer patches ...` Typer subapp."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from matrix_codex.patches import metadata as pm
from matrix_codex.patches.apply import verify_and_apply
from matrix_codex.patches.generate import diff_against_commit, format_patch_range, from_diff
from matrix_codex.patches.store import store
from matrix_codex.settings import get_settings
from matrix_codex.storage.patches_local import LocalPatchStorage

app = typer.Typer(add_completion=False, help="Patch archive (producer side).", no_args_is_help=True)
console = Console()


@app.command("generate")
def generate_cmd(
    repo_dir: Path = typer.Argument(..., help="Working tree containing the changes."),
    upstream_repo: str = typer.Option(..., "--upstream-repo", help="Upstream repository URL."),
    upstream_commit: str = typer.Option(..., "--from", help="Upstream commit the patch applies on top of."),
    to_ref: str = typer.Option("HEAD", "--to", help="Local ref containing the changes."),
    mode: str = typer.Option(
        "diff", "--mode", help="diff (working tree vs upstream) or range (commit range)."
    ),
    mcp_manifest_id: str | None = typer.Option(None, "--mcp"),
    title: str | None = typer.Option(None, "--title"),
    summary: str | None = typer.Option(None, "--summary"),
) -> None:
    """Generate a patch artifact from a working tree or commit range."""

    if mode == "diff":
        body = diff_against_commit(repo_dir, upstream_commit)
    elif mode == "range":
        body = format_patch_range(repo_dir, upstream_commit, to_ref)
    else:
        raise typer.BadParameter("--mode must be 'diff' or 'range'")
    patch = from_diff(
        body,
        upstream_repo=upstream_repo,
        upstream_commit=upstream_commit,
        mcp_manifest_id=mcp_manifest_id,
        title=title,
        summary=summary,
    )
    settings = get_settings()
    backend = LocalPatchStorage(settings.patches_state_dir)
    ref = backend.put(patch)
    console.print_json(data={
        "id": patch.metadata.id,
        "sha256": patch.metadata.sha256,
        "size_bytes": patch.metadata.size_bytes,
        "saved_to": ref,
    })


@app.command("show")
def show_cmd(patch_id: str = typer.Argument(...)) -> None:
    settings = get_settings()
    backend = LocalPatchStorage(settings.patches_state_dir)
    meta = backend.get_metadata(patch_id)
    console.print_json(data=meta.model_dump(mode="json"))


@app.command("verify")
def verify_cmd(patch_id: str = typer.Argument(...)) -> None:
    settings = get_settings()
    backend = LocalPatchStorage(settings.patches_state_dir)
    meta = backend.get_metadata(patch_id)
    body = backend.get_body(patch_id)
    actual_sha = pm.sha256_hex(body)
    ok = actual_sha == meta.sha256
    console.print_json(data={"id": patch_id, "sha256": meta.sha256, "actual": actual_sha, "ok": ok})
    if not ok:
        raise typer.Exit(code=1)


@app.command("store")
def store_cmd(
    patch_id: str = typer.Argument(...),
    authoritative: str = typer.Option("github", "--authoritative"),
    mirrors: str = typer.Option("", "--mirrors", help="Comma-separated mirror backends."),
) -> None:
    """Fan-out write to authoritative backend + mirrors."""

    settings = get_settings()
    backend = LocalPatchStorage(settings.patches_state_dir)
    meta = backend.get_metadata(patch_id)
    body = backend.get_body(patch_id)
    from matrix_codex.patches.metadata import Patch, PatchBody

    patch = Patch(metadata=meta, body=PatchBody(content=body.decode("utf-8", errors="replace")))
    result = store(
        patch,
        authoritative=authoritative,
        mirrors=tuple(m for m in (mirrors.split(",") if mirrors else []) if m),
    )
    console.print_json(data={
        "authoritative": {"backend": result.authoritative_backend, "ref": result.authoritative_ref},
        "mirrors": result.mirror_refs,
        "mirror_errors": result.mirror_errors,
    })


@app.command("apply")
def apply_cmd(
    patch_id: str = typer.Argument(...),
    repo_dir: Path = typer.Argument(...),
) -> None:
    """Apply a stored patch to a working tree (with sha256 verification)."""

    settings = get_settings()
    backend = LocalPatchStorage(settings.patches_state_dir)
    meta = backend.get_metadata(patch_id)
    body = backend.get_body(patch_id)
    verify_and_apply(repo_dir, meta, body)
    console.print(json.dumps({"applied": patch_id, "into": str(repo_dir)}, indent=2))
