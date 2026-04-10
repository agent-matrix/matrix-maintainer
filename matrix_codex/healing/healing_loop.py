from __future__ import annotations

from pathlib import Path

from matrix_codex.analyzers.repo_analyzer import analyze_repo_layout
from matrix_codex.gitpilot.client import GitPilotClient
from matrix_codex.gitpilot.planner import build_fix_prompt
from matrix_codex.healing.failure_classifier import classify_failure
from matrix_codex.healing.fix_strategies import apply_fixes
from matrix_codex.healing.retry_policy import should_retry
from matrix_codex.matrixlab.verifier import verify_repo
from matrix_codex.models import RepoHealthReport
from matrix_codex.settings import Settings


def run_healing_loop(report: RepoHealthReport, repo_dir: Path, settings: Settings) -> RepoHealthReport:
    gitpilot = GitPilotClient(settings)

    attempt = 0
    while True:
        analyze_repo_layout(report, repo_dir)
        verify_repo(report, repo_dir, settings)
        if report.status == "healthy":
            return report

        if not should_retry(attempt, settings.max_fix_attempts):
            report.notes.append(f"max fix attempts reached ({settings.max_fix_attempts})")
            report.finalize_status()
            return report

        report.fix_attempts += 1
        attempt += 1

        if gitpilot.available():
            _ = gitpilot.run_headless(report.repo.full_name, build_fix_prompt(report, str(repo_dir)), report.branch_name)

        changed = apply_fixes(report, repo_dir)
        report.changed_files = sorted(set(report.changed_files + changed))
        report.notes.append(f"attempt {attempt}: applied {classify_failure(report)} local fixes")
