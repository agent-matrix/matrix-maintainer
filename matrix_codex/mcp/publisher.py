"""Persist and publish a verified MCP manifest.

For now "publish" is a local write -- the actual push to MatrixHub is
a Phase-5 follow-up that we wire as a separate adapter so the publish
step stays a single CLI call.
"""

from __future__ import annotations

import json
from pathlib import Path

from matrix_codex.mcp.manifest import MCPManifest


def state_path(state_dir: Path, manifest: MCPManifest) -> Path:
    return state_dir / f"{manifest.id}.json"


def save(state_dir: Path, manifest: MCPManifest) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    out = state_path(state_dir, manifest)
    out.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    return out


def load(state_dir: Path, manifest_id: str) -> MCPManifest:
    path = state_dir / f"{manifest_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"no manifest at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return MCPManifest.model_validate(data)


def publish(state_dir: Path, manifest: MCPManifest) -> Path:
    """Stamp the manifest as published and save.

    Returns the manifest path. The actual MatrixHub push is performed
    by `matrix_codex.matrixhub.publisher` in a follow-up phase.
    """

    if "agent-matrix-verified" not in manifest.tags.quality and manifest.status.health == "verified":
        manifest.tags.quality.append("agent-matrix-verified")
    manifest.touch()
    return save(state_dir, manifest)
