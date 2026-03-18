from __future__ import annotations

from matrix_maintainer.models import RepoHealthReport

def build_fix_prompt(report: RepoHealthReport, repo_path: str) -> str:
    return f"""Analyze repository {report.repo.full_name} at {repo_path}.

The goal is to make the repository conform to these standards:
- Makefile with install/test/start
- pyproject.toml with Python 3.11 and uv
- tests/test_health.py
- make install passes
- make test passes
- make start passes as a smoke check

Current failures:
- install_ok={report.install_ok}
- test_ok={report.test_ok}
- start_ok={report.start_ok}
- notes={report.notes}

Propose the minimum safe code and configuration changes required.
Output a concise patch plan.
"""
