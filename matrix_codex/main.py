from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from uuid import uuid4

from matrix_codex.agent_matrix.init import check_budget, check_guardian_approval, get_plan_from_matrix_ai
from matrix_codex.health_scanner import HealthScanner, ScannerConfig
from matrix_codex.inventory.filters import include_repo
from matrix_codex.inventory.org_discovery import GitHubOrgDiscovery
from matrix_codex.inventory.repo_inventory import save_inventory
from matrix_codex.models import HealthIssue, MaintenanceTask, RepoHealthReport, RepoRef
from matrix_codex.orchestration.dispatcher import dispatch_worker_workflow
from matrix_codex.reporting.history_builder import write_history
from matrix_codex.site.generator import generate_site
from matrix_codex.storage.models import EventRecord, HealthScanRecord, RunRecord, StorageDB, TaskRecord
from matrix_codex.task_engine import create_tasks
from matrix_codex.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def check_single_repo(repo: RepoRef, settings: Settings) -> RepoHealthReport:
    report = RepoHealthReport(repo=repo)
    report.notes.append("local_check_deprecated_use_scan_health")
    report.finalize_status()
    return report


def scan_health(settings: Settings) -> list[HealthIssue]:
    scanner = HealthScanner(ScannerConfig(repositories_file=Path("config/repositories.yml")))
    issues = scanner.scan()
    db = StorageDB(settings.state_dir / "maintainer_records.json")
    for issue in issues:
        db.append(
            "health_scans",
            HealthScanRecord(
                scan_id=str(uuid4()),
                repo=issue.repo,
                issue_type=issue.issue_type,
                severity=issue.severity,
                details=issue.details,
            ),
        )
    return issues


def plan_maintenance(settings: Settings, issues: list[HealthIssue]) -> list[MaintenanceTask]:
    tasks = create_tasks(issues, Path("config/tasks.yml"))
    approved: list[MaintenanceTask] = []
    db = StorageDB(settings.state_dir / "maintainer_records.json")

    for task in tasks:
        plan = get_plan_from_matrix_ai(task)
        task.metadata["matrix_ai_plan"] = plan
        if not check_guardian_approval(task, max_files=settings.max_autofix_files):
            continue
        if not check_budget(task, available_mxu=5.0):
            continue
        approved.append(task)
        db.append(
            "tasks",
            TaskRecord(
                task_id=str(uuid4()),
                run_id=task.metadata.get("run_id", ""),
                repo=task.repo,
                task_type=task.task_type,
                status="approved",
                risk_level=task.risk_level,
            ),
        )
    return approved


def run_maintenance(settings: Settings, tasks: list[MaintenanceTask], controller_run_id: str | None = None) -> list[RepoHealthReport]:
    reports: list[RepoHealthReport] = []
    token = settings.cross_repo_token or settings.github_token
    db = StorageDB(settings.state_dir / "maintainer_records.json")

    for task in tasks:
        repo_name = task.repo.split("/")[-1]
        repo = RepoRef(name=repo_name, full_name=task.repo, clone_url=f"https://github.com/{task.repo}.git")
        report = RepoHealthReport(repo=repo, operation=task.task_type, controller_run_id=controller_run_id)
        if not token:
            report.notes.append("dispatch_skipped=missing_token")
            report.finalize_status()
            reports.append(report)
            continue

        patched = settings.model_copy(update={"github_token": token})
        result = dispatch_worker_workflow(
            settings=patched,
            repo_full_name=task.repo,
            operation=task.task_type,
            base_branch=repo.default_branch,
            controller_run_id=controller_run_id,
            task=task,
        )
        report.dispatch_ok = result.ok
        report.worker_url = result.worker_url
        if result.error:
            report.notes.append(result.error)
        report.notes.append("dispatch_ok" if result.ok else "dispatch_failed")
        report.finalize_status()
        reports.append(report)

        db.append(
            "runs",
            RunRecord(
                run_id=controller_run_id or str(uuid4()),
                repo=task.repo,
                status="dispatched" if result.ok else "failed",
                operation=task.task_type,
            ),
        )
        db.append(
            "events",
            EventRecord(
                event_id=str(uuid4()),
                run_id=controller_run_id or "",
                repo=task.repo,
                status="dispatched" if result.ok else "failed",
                payload={"worker_url": result.worker_url, "error": result.error},
            ),
        )

    return reports


def run_daily(settings: Settings) -> list[RepoHealthReport]:
    settings.ensure_directories()
    discovery = GitHubOrgDiscovery(settings)
    repos = [repo for repo in discovery.list_repositories() if include_repo(repo)]
    save_inventory(settings, repos)

    controller_run_id = os.getenv("GITHUB_RUN_ID", str(uuid4()))
    issues = scan_health(settings)
    tasks = plan_maintenance(settings, issues)
    reports = run_maintenance(settings, tasks, controller_run_id)

    latest_path = settings.state_dir / "latest_status.json"
    latest_path.write_text(json.dumps({"items": [r.model_dump(mode="json") for r in reports]}, indent=2), encoding="utf-8")
    write_history(settings.state_dir / "history_index.json", reports)
    generate_site(settings)
    return reports


def run_daily_main() -> int:
    settings = get_settings()
    run_daily(settings)
    return 0
