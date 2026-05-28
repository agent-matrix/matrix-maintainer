from __future__ import annotations

from matrix_codex.observability.metrics import readiness_probe
from matrix_codex.settings import Settings


def test_readiness_probe_ok_with_writable_dirs(tmp_path) -> None:
    settings = Settings(
        STATE_DIR=str(tmp_path / "state"),
        WORK_DIR=str(tmp_path / "work"),
        MCP_STATE_DIR=str(tmp_path / "mcp"),
        PATCHES_STATE_DIR=str(tmp_path / "patches"),
    )
    result = readiness_probe(settings)
    assert result["ready"] is True
    assert result["checks"]["state_dir"]["ok"] is True
