"""Discover and import an upstream MCP server into a manifest skeleton.

The `import_upstream` entry point is intentionally side-effect-free
with respect to network when the caller passes ``probe=False``. The
verify / repair steps perform the actual sandbox work via the
SelfRepair client.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from matrix_codex.mcp.license import LicenseDecision, decide
from matrix_codex.mcp.manifest import MCPManifest, MCPSource, MCPStatus, MCPTags


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    return s or "unnamed"


def parse_repo_url(url: str) -> tuple[str, str]:
    """Return (owner, repo) extracted from a GitHub-style URL."""

    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"cannot parse owner/repo from {url!r}")
    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def import_upstream(
    url: str,
    *,
    title: str | None = None,
    summary: str | None = None,
    license_id: str | None = None,
    commit: str | None = None,
    capabilities: list[str] | None = None,
) -> tuple[MCPManifest, LicenseDecision]:
    """Build a fresh manifest skeleton for an upstream MCP server."""

    owner, repo = parse_repo_url(url)
    manifest_id = slugify(f"{owner}-{repo}")
    manifest = MCPManifest(
        id=manifest_id,
        title=title or repo,
        summary=summary or f"Imported from {url}",
        source=MCPSource(repo=url, commit=commit, license_id=license_id),
        tags=MCPTags(capability=capabilities or []),
        status=MCPStatus(health="unverified", notes=["imported"]),
    )
    license_decision = decide(license_id)
    return manifest, license_decision
