"""Deterministic tag inference for an MCP server.

Given the contents of a few well-known files (package.json,
pyproject.toml, Dockerfile, README front-matter, the project's actual
file tree), produce capability / runtime / quality tags that we can
attach to the manifest.

Keep it deterministic -- this is the ground truth that all downstream
policy decisions are made against. No LLM here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from matrix_codex.mcp.manifest import MCPTags, QualityTag, RiskTag, RuntimeTag

_RUNTIME_FILES: dict[str, RuntimeTag] = {
    "package.json": "node",
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "setup.py": "python",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "build.gradle": "jvm",
    "pom.xml": "jvm",
    "Dockerfile": "docker",
    "Dockerfile.backend": "docker",
}

_TEST_HINTS = ("tests/", "test/", "__tests__/", "spec/", "pytest.ini", "jest.config")
_CI_HINTS = (".github/workflows/", ".gitlab-ci.yml", "azure-pipelines.yml", "circle.yml", ".circleci/")


def _file_tree_runtimes(tree: Iterable[str]) -> list[RuntimeTag]:
    found: list[RuntimeTag] = []
    for path in tree:
        for marker, runtime in _RUNTIME_FILES.items():
            if path.endswith(marker) and runtime not in found:
                found.append(runtime)
    if not found:
        found = ["other"]
    return found


def _quality(tree: list[str]) -> list[QualityTag]:
    q: list[QualityTag] = []
    tree_str = "\n".join(tree).lower()
    if any(h in p for p in tree for h in _TEST_HINTS):
        q.append("has-tests")
    if any(h in p for p in tree for h in _CI_HINTS):
        q.append("has-ci")
    if "readme.md" in tree_str or "readme.rst" in tree_str:
        q.append("has-readme")
    if "license" in tree_str:
        q.append("has-license")
    if "py.typed" in tree_str or "tsconfig.json" in tree_str:
        q.append("has-typing")
    return q


def _risk_from_dependencies(
    package_json: dict[str, Any] | None,
    pyproject_dependencies: list[str],
) -> list[RiskTag]:
    risk: list[RiskTag] = []
    deps_text: list[str] = []
    if package_json:
        deps_text.extend((package_json.get("dependencies") or {}).keys())
        deps_text.extend((package_json.get("devDependencies") or {}).keys())
    deps_text.extend(pyproject_dependencies)
    blob = " ".join(deps_text).lower()
    if any(token in blob for token in ("http", "axios", "requests", "httpx", "urllib3", "fetch")):
        risk.append("network-access")
    if any(token in blob for token in ("sqlite", "redis", "postgres", "mongodb", "sqlalchemy")):
        risk.append("persistent-state")
    if any(token in blob for token in ("openai", "anthropic", "google-cloud", "aws-sdk", "boto3", "stripe")):
        risk.append("third-party-api")
    return risk


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _read_pyproject_deps(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        try:
            import tomllib  # type: ignore[import-not-found]
        except ImportError:
            return []
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        deps = data.get("project", {}).get("dependencies", []) or []
        return [str(d) for d in deps]
    except Exception:  # noqa: BLE001
        return []


def infer_tags(
    repo_dir: Path,
    *,
    capabilities: list[str] | None = None,
) -> MCPTags:
    """Walk a checked-out repo and infer manifest tags."""

    if not repo_dir.exists():
        return MCPTags(capability=capabilities or [])

    tree: list[str] = []
    for p in repo_dir.rglob("*"):
        if any(part.startswith(".") for part in p.parts):
            # skip vendored / hidden trees but keep .github intentionally
            if ".github/workflows" not in str(p):
                continue
        rel = p.relative_to(repo_dir).as_posix()
        tree.append(rel)

    runtime = _file_tree_runtimes(tree)
    quality = _quality(tree)
    pkg = _read_json(repo_dir / "package.json")
    py_deps = _read_pyproject_deps(repo_dir / "pyproject.toml")
    risk = _risk_from_dependencies(pkg, py_deps)

    return MCPTags(
        capability=capabilities or [],
        runtime=runtime,
        risk=risk,
        quality=quality,
        maintenance=[],
    )
