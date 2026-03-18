from __future__ import annotations

from pathlib import Path

from matrix_maintainer.models import RepoHealthReport, StandardCheck
from matrix_maintainer.standards.python311_rules import ensure_python311
from matrix_maintainer.standards.uv_rules import ensure_uv


def analyze_repo_layout(report: RepoHealthReport, repo_dir: Path) -> RepoHealthReport:
    makefile = repo_dir / "Makefile"
    pyproject = repo_dir / "pyproject.toml"
    health_test = repo_dir / "tests" / "test_health.py"

    report.makefile_ok = makefile.exists()
    report.pyproject_ok = pyproject.exists()
    report.health_test_ok = health_test.exists()
    report.python311_ok = ensure_python311(pyproject) if pyproject.exists() else False
    report.uv_ok = ensure_uv(pyproject) if pyproject.exists() else False

    report.checks = [
        StandardCheck(name="makefile", ok=report.makefile_ok),
        StandardCheck(name="pyproject", ok=report.pyproject_ok),
        StandardCheck(name="health_test", ok=report.health_test_ok),
        StandardCheck(name="python311", ok=report.python311_ok),
        StandardCheck(name="uv", ok=report.uv_ok),
    ]
    return report
