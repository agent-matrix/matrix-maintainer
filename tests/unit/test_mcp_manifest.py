from __future__ import annotations

import json
from pathlib import Path

import pytest

from matrix_codex.mcp import publisher as pub
from matrix_codex.mcp.discovery import import_upstream, parse_repo_url, slugify
from matrix_codex.mcp.manifest import MCPManifest, SCHEMA_VERSION


def test_parse_repo_url_basic() -> None:
    assert parse_repo_url("https://github.com/foo/bar") == ("foo", "bar")
    assert parse_repo_url("https://github.com/foo/bar.git") == ("foo", "bar")
    assert parse_repo_url("https://github.com/foo/bar/issues") == ("foo", "bar")


def test_parse_repo_url_invalid() -> None:
    with pytest.raises(ValueError):
        parse_repo_url("https://github.com/onlyowner")


def test_slugify() -> None:
    assert slugify("foo bar") == "foo-bar"
    assert slugify("MIXED_CaSe") == "mixed-case"


def test_import_upstream_returns_manifest_skeleton() -> None:
    manifest, decision = import_upstream(
        "https://github.com/example/github-mcp-server",
        license_id="MIT",
        capabilities=["github", "repo-management"],
    )
    assert manifest.schema_version == SCHEMA_VERSION
    assert manifest.id == "example-github-mcp-server"
    assert manifest.source.license_id == "MIT"
    assert manifest.tags.capability == ["github", "repo-management"]
    assert decision.allowed is True


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    manifest, _ = import_upstream("https://github.com/foo/bar", license_id="Apache-2.0")
    path = pub.save(tmp_path, manifest)
    assert path.is_file()
    loaded = pub.load(tmp_path, manifest.id)
    assert loaded.id == manifest.id
    assert loaded.source.license_id == "Apache-2.0"


def test_publish_stamps_verified(tmp_path: Path) -> None:
    manifest, _ = import_upstream("https://github.com/foo/bar", license_id="MIT")
    manifest.status.health = "verified"
    pub.save(tmp_path, manifest)
    path = pub.publish(tmp_path, manifest)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "agent-matrix-verified" in data["tags"]["quality"]
