from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from matrix_codex.health_scanner import HealthScanner, ScannerConfig
from matrix_codex.inventory.org_discovery import GitHubOrgDiscovery
from matrix_codex.main import check_single_repo, plan_maintenance, run_daily, run_maintenance, scan_health
from matrix_codex.models import MaintenanceTask
from matrix_codex.reporting.status_builder import build_status
from matrix_codex.settings import get_settings
from matrix_codex.logging import configure_logging
from matrix_codex.site.generator import generate_site
from matrix_codex.storage.models import StorageDB
from matrix_codex.task_engine import create_tasks

app = typer.Typer(add_completion=False, help="matrix-codex CLI")
console = Console()


@app.callback()
def _callback() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command("discover")
def discover() -> None:
    settings = get_settings()
    repos = GitHubOrgDiscovery(settings).list_repositories()
    table = Table(title="Repositories")
    table.add_column("Name")
    table.add_column("Default branch")
    for repo in repos:
        table.add_row(repo.full_name, repo.default_branch)
    console.print(table)


@app.command("scan-health")
def scan_health_cmd() -> None:
    settings = get_settings()
    issues = scan_health(settings)
    console.print_json(data={"issues": [issue.model_dump(mode="json") for issue in issues]})


@app.command("plan-maintenance")
def plan_maintenance_cmd() -> None:
    settings = get_settings()
    scanner = HealthScanner(ScannerConfig(repositories_file=Path("config/repositories.yml")))
    issues = scanner.scan()
    tasks = plan_maintenance(settings, issues)
    console.print_json(data={"tasks": [task.model_dump(mode="json") for task in tasks]})


@app.command("run-maintenance")
def run_maintenance_cmd(task_json: str = typer.Option("", help="Optional single task payload as JSON.")) -> None:
    settings = get_settings()
    if task_json:
        task = MaintenanceTask.model_validate(json.loads(task_json))
        reports = run_maintenance(settings, [task])
    else:
        issues = scan_health(settings)
        tasks = create_tasks(issues, Path("config/tasks.yml"))
        reports = run_maintenance(settings, tasks)
    console.print_json(data={"reports": [r.model_dump(mode="json") for r in reports]})


@app.command("report-status")
def report_status_cmd() -> None:
    settings = get_settings()
    db = StorageDB(settings.state_dir / "maintainer_records.json")
    status = build_status(settings)
    status["maintainer"] = {
        "runs": len(db.list("runs")),
        "tasks": len(db.list("tasks")),
        "events": len(db.list("events")),
    }
    (settings.state_dir / "latest_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    generate_site(settings)
    console.print("Status updated")


@app.command("run-daily")
def run_daily_cmd() -> None:
    settings = get_settings()
    reports = run_daily(settings)
    console.print(f"Processed {len(reports)} maintenance tasks")


@app.command("publish-site")
def publish_site() -> None:
    settings = get_settings()
    generate_site(settings)
    console.print("Status site generated")


@app.command("check-repo")
def check_repo(repo_name: str) -> None:
    settings = get_settings()
    repo = next((r for r in GitHubOrgDiscovery(settings).list_repositories() if r.name == repo_name or r.full_name == repo_name), None)
    if repo is None:
        raise typer.Exit(f"Repository not found: {repo_name}")
    report = check_single_repo(repo, settings)
    console.print_json(data=report.model_dump(mode="json"))


if __name__ == "__main__":
    app()
