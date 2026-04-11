from __future__ import annotations

import json
import logging
import os

from matrix_codex.analyzers.repo_analyzer import analyze_repo_layout
from matrix_codex.governance.branch_rules import build_branch_name
from matrix_codex.governance.policy_engine import evaluate_policy
from matrix_codex.healing.healing_loop import run_healing_loop
from matrix_codex.inventory.filters import include_repo
from matrix_codex.inventory.org_discovery import GitHubOrgDiscovery
from matrix_codex.inventory.repo_inventory import save_inventory
from matrix_codex.matrixlab.sandbox import SandboxManager
from matrix_codex.models import RepoHealthReport, RepoRef
from matrix_codex.orchestration.dispatcher import dispatch_worker_workflow
from matrix_codex.reporting.history_builder import write_history
from matrix_codex.site.generator import generate_site
from matrix_codex.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def check_single_repo(repo: RepoRef, settings: Settings) -> RepoHealthReport:
    sandbox = SandboxManager(settings)
    repo_dir = sandbox.clone_repo(repo)
    report = RepoHealthReport(repo=repo, branch_name=build_branch_name(repo.name))
    analyze_repo_layout(report, repo_dir)
    report = run_healing_loop(report, repo_dir, settings)
    policy = evaluate_policy(report.changed_files)
    report.notes.append(f"policy_risk={policy['risk']}")
    return report


def dispatch_single_repo(repo: RepoRef, settings: Settings, operation: str, controller_run_id: str | None = None) -> RepoHealthReport:
    report = RepoHealthReport(repo=repo, operation=operation, controller_run_id=controller_run_id)
    token = settings.cross_repo_token or settings.github_token
    if not token:
        report.notes.append("dispatch_skipped=missing_token")
        report.finalize_status()
        return report

    patched = settings.model_copy(update={"github_token": token})
    result = dispatch_worker_workflow(
        settings=patched,
        repo_full_name=repo.full_name,
        operation=operation,
        base_branch=repo.default_branch,
        controller_run_id=controller_run_id,
    )
    report.dispatch_ok = result.ok
    report.worker_url = result.worker_url
    if result.error:
        report.notes.append(result.error)
    if result.ok:
        report.status = "unknown"
        report.notes.append("dispatch_ok")
    else:
        report.finalize_status()
    return report


def run_daily(settings: Settings) -> list[RepoHealthReport]:
    settings.ensure_directories()
    discovery = GitHubOrgDiscovery(settings)
    repos = [repo for repo in discovery.list_repositories() if include_repo(repo)]
    save_inventory(settings, repos)

    execution_mode = os.getenv("MATRIX_CODEX_EXECUTION_MODE", "dispatch").lower()
    operation = os.getenv("MATRIX_CODEX_OPERATION", "daily-maintenance")
    controller_run_id = os.getenv("GITHUB_RUN_ID")

    reports: list[RepoHealthReport] = []
    for repo in repos:
        try:
            if execution_mode == "local":
                reports.append(check_single_repo(repo, settings))
            else:
                reports.append(dispatch_single_repo(repo, settings, operation, controller_run_id))
        except Exception as exc:  # pragma: no cover
            report = RepoHealthReport(repo=repo, status="down", operation=operation, controller_run_id=controller_run_id)
            report.notes.append(f"unhandled_error={exc}")
            report.finalize_status()
            reports.append(report)

    latest_path = settings.state_dir / "latest_status.json"
    latest_path.write_text(json.dumps({"items": [r.model_dump(mode="json") for r in reports]}, indent=2), encoding="utf-8")
    write_history(settings.state_dir / "history_index.json", reports)
    generate_site(settings)
    return reports


def run_daily_main() -> int:
    settings = get_settings()
    run_daily(settings)
    return 0
