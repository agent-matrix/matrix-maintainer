from __future__ import annotations

import json
import logging
from pathlib import Path

from matrix_maintainer.analyzers.repo_analyzer import analyze_repo_layout
from matrix_maintainer.governance.branch_rules import build_branch_name
from matrix_maintainer.governance.policy_engine import evaluate_policy
from matrix_maintainer.healing.healing_loop import run_healing_loop
from matrix_maintainer.inventory.filters import include_repo
from matrix_maintainer.inventory.org_discovery import GitHubOrgDiscovery
from matrix_maintainer.inventory.repo_inventory import save_inventory
from matrix_maintainer.matrixlab.sandbox import SandboxManager
from matrix_maintainer.models import RepoHealthReport, RepoRef
from matrix_maintainer.reporting.history_builder import write_history
from matrix_maintainer.site.generator import generate_site
from matrix_maintainer.settings import Settings, get_settings

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


def run_daily(settings: Settings) -> list[RepoHealthReport]:
    discovery = GitHubOrgDiscovery(settings)
    repos = [repo for repo in discovery.list_repositories() if include_repo(repo)]
    save_inventory(settings, repos)

    reports: list[RepoHealthReport] = []
    for repo in repos:
        try:
            reports.append(check_single_repo(repo, settings))
        except Exception as exc:  # pragma: no cover
            report = RepoHealthReport(repo=repo, status="down")
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
