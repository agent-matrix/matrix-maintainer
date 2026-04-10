from pathlib import Path

from matrix_codex.gitpilot.patcher import apply_safe_local_fixes
from matrix_codex.models import RepoHealthReport

def apply_fixes(report: RepoHealthReport, repo_dir: Path) -> list[str]:
    return apply_safe_local_fixes(report, repo_dir)
