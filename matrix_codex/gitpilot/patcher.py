from __future__ import annotations

from pathlib import Path

from matrix_codex.models import RepoHealthReport
from matrix_codex.standards.makefile_rules import ensure_makefile
from matrix_codex.standards.pyproject_rules import ensure_pyproject
from matrix_codex.standards.health_test_rules import ensure_health_test


def apply_safe_local_fixes(report: RepoHealthReport, repo_dir: Path) -> list[str]:
    changed: list[str] = []
    _, c1 = ensure_makefile(repo_dir)
    _, c2 = ensure_pyproject(repo_dir, report.repo.name)
    _, c3 = ensure_health_test(repo_dir)
    changed.extend(c1 + c2 + c3)
    return sorted(set(changed))
