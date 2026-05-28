from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    # Keep tests hermetic: never read the user's real .env, and write
    # state into a tmp dir.
    monkeypatch.setenv("STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("WORK_DIR", str(tmp_path / "work"))
    monkeypatch.setenv("STATUS_SITE_DIR", str(tmp_path / "status-site"))
    monkeypatch.setenv("MCP_STATE_DIR", str(tmp_path / "mcp"))
    monkeypatch.setenv("PATCHES_STATE_DIR", str(tmp_path / "patches"))
    # Clear potentially leaking credentials.
    for var in (
        "OLLABRIDGE_API_KEY",
        "OPENAI_API_KEY",
        "SELFREPAIR_API_KEY",
        "GITHUB_TOKEN",
    ):
        monkeypatch.delenv(var, raising=False)
    # Drop the get_settings lru cache so each test sees fresh settings.
    from matrix_codex.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def respx_mock():
    pytest.importorskip("respx")
    import respx as _respx

    with _respx.mock(assert_all_called=False) as m:
        yield m
