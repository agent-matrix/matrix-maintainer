"""MCP server maintenance surface.

This package implements the "Surface B" workflow from the design doc:
import an upstream MCP server, generate and tag a manifest, gate by
license policy, verify in a sandbox via SelfRepair, repair (safe -> AI
escalation), and publish to MatrixHub.

The public API is the CLI under :mod:`matrix_codex.mcp.cli`. Programmatic
use can import from the per-step modules below.
"""

from matrix_codex.mcp.manifest import MCPManifest, MCPSource, MCPStatus, MCPTags, SCHEMA_VERSION

__all__ = ["MCPManifest", "MCPSource", "MCPStatus", "MCPTags", "SCHEMA_VERSION"]
