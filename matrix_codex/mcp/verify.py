"""Sandbox verification for an MCP server -- routes through SelfRepair.

No runtime execution in this module. Every install / test / health
check goes through the SelfRepair client so we share the sandbox and
policy enforcement with the rest of matrix-maintainer.
"""

from __future__ import annotations

from matrix_codex.mcp.manifest import MCPManifest
from matrix_codex.selfrepair import SelfRepairClient
from matrix_codex.selfrepair.dto import RepoRefDTO, ValidationReportDTO


def verify(
    manifest: MCPManifest,
    client: SelfRepairClient,
    *,
    default_branch: str = "main",
) -> tuple[MCPManifest, ValidationReportDTO]:
    """Validate the MCP server and update its manifest status in place."""

    ref = RepoRefDTO(
        full_name=str(manifest.source.repo).rstrip("/").split("github.com/", 1)[-1],
        clone_url=str(manifest.source.repo),
        default_branch=default_branch,
    )
    result = client.validate(ref, in_sandbox=True)

    manifest.status.health = "verified" if result.ok else "broken"
    if result.ok:
        manifest.status.latest_verified_commit = manifest.source.commit
        from datetime import datetime, timezone

        manifest.status.latest_verified_at = datetime.now(timezone.utc).isoformat()
    if "selfrepair-scanned" not in manifest.tags.maintenance:
        manifest.tags.maintenance.append("selfrepair-scanned")
    manifest.status.notes.extend(result.notes)
    manifest.touch()
    return manifest, result
