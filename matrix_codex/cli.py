from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import typer
from rich.console import Console
from rich.table import Table

from matrix_codex.health_scanner import HealthScanner, ScannerConfig
from matrix_codex.inventory.org_discovery import GitHubOrgDiscovery
from matrix_codex.logging import configure_logging
from matrix_codex.main import check_single_repo, plan_maintenance, run_daily, run_maintenance, scan_health
from matrix_codex.mcp.cli import app as mcp_app
from matrix_codex.models import MaintenanceTask
from matrix_codex.orchestration.pr_body import render as render_pr_body
from matrix_codex.orchestration.reports import write_org_scan, write_repair
from matrix_codex.patches.cli import app as patches_app
from matrix_codex.reporting.status_builder import build_status
from matrix_codex.selfrepair import get_client as get_selfrepair_client
from matrix_codex.selfrepair.dto import (
    HealthIssueDTO,
    JsonReportDTO,
    RepoHealthReportDTO,
    RepoRefDTO,
)
from matrix_codex.settings import get_settings
from matrix_codex.site.generator import generate_site
from matrix_codex.storage.models import StorageDB
from matrix_codex.task_engine import create_tasks

app = typer.Typer(
    add_completion=False,
    help="matrix-maintainer CLI (engine codename: matrix-codex)",
    no_args_is_help=True,
)
console = Console()

# Register subcommand groups.
app.add_typer(mcp_app, name="mcp", help="MCP server maintenance (Surface B).")
app.add_typer(patches_app, name="patches", help="Patch archive producer.")


@app.callback()
def _callback() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


# ---------------------------------------------------------------------------
# Legacy commands (preserved verbatim, used by the daily orchestrator)
# ---------------------------------------------------------------------------


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


@app.command("submit-maintenance")
def submit_maintenance_cmd(
    repo: str = typer.Option("", help="owner/name or URL; omit to submit all inventory repos"),
    mode: str = typer.Option("dry_run", help="dry_run | draft_pr"),
    repos_file: str = typer.Option("config/repos.yml", help="Inventory file when --repo is omitted"),
) -> None:
    """Submit dry-run maintenance request(s) to SelfRepair's control plane.

    Matrix-Maintainer sends intent; SelfRepair records it (inbox/notification)
    and runs the health check. Requires SELFREPAIR_INGEST_TOKEN.
    """
    from matrix_codex.control_plane import submit_maintenance_request

    if repo:
        targets = [{"name": repo, "default_branch": "main"}]
    else:
        import yaml

        data = yaml.safe_load(Path(repos_file).read_text(encoding="utf-8")) or {}
        targets = data.get("repositories", []) or []

    results = []
    for item in targets:
        name = item.get("name")
        if not name:
            continue
        try:
            res = submit_maintenance_request(name, branch=item.get("default_branch", "main"), mode=mode)
            results.append({"repo": name, **res})
            console.print(f"submitted {name}: job={res.get('job_id')} status={res.get('status')}")
        except Exception as exc:  # noqa: BLE001 — report and continue per repo
            console.print(f"[red]failed {name}: {exc}[/red]")
    console.print_json(data={"submitted": results})


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


@app.command("check-make")
def check_make(
    targets: list[str] = typer.Argument(  # noqa: B008
        None, help="Make targets to run, in order. Default: install test."
    ),
    cwd: Path = typer.Option(  # noqa: B008
        Path.cwd(),
        "--cwd",
        help="Working directory of the target repository (default: cwd).",
    ),
    output: Path | None = typer.Option(None, "--output"),
    repo: str | None = typer.Option(None, "--repo"),
) -> None:
    """Run `make <target>` in order; emit a structured JSON report."""
    import os
    import shlex
    import subprocess
    import datetime as _dt

    if not targets:
        targets = ["install", "test"]

    repo_id = repo or os.environ.get("GITHUB_REPOSITORY") or "(unknown)"
    started_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
    steps_report: list[dict] = []
    overall_status = "ok"
    failed_step: str | None = None

    for target in targets:
        cmd = ["make", target]
        console.log(f"[matrix-maintainer] running: {shlex.join(cmd)} (cwd={cwd})")
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
        steps_report.append(
            {
                "target": target,
                "exit_code": proc.returncode,
                "stdout_tail": proc.stdout[-2000:],
                "stderr_tail": proc.stderr[-2000:],
            }
        )
        if proc.returncode != 0:
            overall_status = "failed"
            failed_step = target
            break

    report = {
        "schema_version": "0.1",
        "source": "matrix-maintainer.cli",
        "type": "maintenance.check.completed",
        "repo": repo_id,
        "started_at": started_at,
        "finished_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "targets": targets,
        "status": overall_status,
        "failed_step": failed_step,
        "steps": steps_report,
    }
    text = json.dumps(report, indent=2)
    if output:
        output.write_text(text + "\n", encoding="utf-8")
    console.print(text)
    raise typer.Exit(code=0 if overall_status == "ok" else 1)


# ---------------------------------------------------------------------------
# Phase 2 -- user-facing commands (scan-org / repair-repo / repair-org)
# ---------------------------------------------------------------------------


def _repo_ref(full_name: str, *, default_branch: str = "main") -> RepoRefDTO:
    return RepoRefDTO(
        full_name=full_name,
        clone_url=f"https://github.com/{full_name}.git",
        default_branch=default_branch,
    )


@app.command("scan-org")
def scan_org_cmd(
    org: str = typer.Argument(..., help="GitHub organization name (e.g. agent-matrix)."),
    report_only: bool = typer.Option(False, "--report-only"),
) -> None:
    """Scan every repo in an organization via the SelfRepair client."""

    settings = get_settings()
    if settings.github_org != org:
        settings = settings.model_copy(update={"github_org": org})

    repos = GitHubOrgDiscovery(settings).list_repositories()
    client = get_selfrepair_client(settings)

    health_reports: list[RepoHealthReportDTO] = []
    for repo in repos:
        ref = _repo_ref(repo.full_name, default_branch=repo.default_branch)
        try:
            report = client.scan(ref)
        except Exception as exc:  # noqa: BLE001
            report = RepoHealthReportDTO(repo=ref, status="unknown", notes=[f"scan_error: {exc}"])
        health_reports.append(report)

    path = write_org_scan(settings.state_dir, org, health_reports)
    table = Table(title=f"scan-org {org}")
    table.add_column("Repository")
    table.add_column("Status")
    table.add_column("Issues")
    for r in health_reports:
        table.add_row(r.repo.full_name, r.status, str(len(r.issues)))
    console.print(table)
    console.print(f"\nReport written: [bold]{path}[/bold]")

    if not report_only:
        console.print("[dim]Use repair-org or repair-repo to act on these findings.[/dim]")


@app.command("repair-repo")
def repair_repo_cmd(
    full_name: str = typer.Argument(...),
    safe_only: bool = typer.Option(True, "--safe-only/--all-fixers"),
    open_draft_pr: bool = typer.Option(False, "--open-draft-pr"),
    use_gitpilot: bool = typer.Option(False, "--use-gitpilot"),
) -> None:
    """Scan + repair a single repository via SelfRepair (and optionally GitPilot)."""

    settings = get_settings()
    client = get_selfrepair_client(settings)
    ref = _repo_ref(full_name)

    health = client.scan(ref)
    repair_result = client.repair(ref, health.issues, safe_only=safe_only)
    validation = None
    if repair_result.applied:
        validation = client.validate(ref, in_sandbox=True)

    report = JsonReportDTO(
        repo=full_name, health=health, repair=repair_result, validation=validation
    )
    path = write_repair(settings.state_dir, report)

    risk = "high" if any(i.severity in {"high", "critical"} for i in health.issues) else "medium"
    body = render_pr_body(
        report=report,
        risk_level=risk,
        operation="repair",
        use_gitpilot=use_gitpilot,
    )
    body_path = path.with_suffix(".pr.md")
    body_path.write_text(body, encoding="utf-8")

    console.print_json(data=report.model_dump(mode="json"))
    console.print(f"\nReport: [bold]{path}[/bold]")
    console.print(f"PR body: [bold]{body_path}[/bold]")

    if open_draft_pr:
        from matrix_codex.orchestration.dispatcher import dispatch_worker_workflow

        if not (settings.github_token or settings.cross_repo_token):
            console.print("[red]Cannot dispatch worker: GITHUB_TOKEN / CROSS_REPO_TOKEN not set.[/red]")
            raise typer.Exit(code=2)
        task = MaintenanceTask(
            repo=full_name,
            issue_type="orchestrator_repair",
            task_type="repair_gitpilot" if use_gitpilot else "repair_safe",
            risk_level=risk,
            metadata={"safe_only": safe_only, "use_gitpilot": use_gitpilot, "pr_body": body},
        )
        controller_run_id = str(uuid4())
        result = dispatch_worker_workflow(
            settings=settings.model_copy(update={
                "github_token": settings.cross_repo_token or settings.github_token
            }),
            repo_full_name=full_name,
            operation=task.task_type,
            controller_run_id=controller_run_id,
            task=task,
        )
        console.print(
            f"Dispatch: ok={result.ok} url={result.worker_url} error={result.error}"
        )


@app.command("repair-org")
def repair_org_cmd(
    org: str = typer.Argument(...),
    safe_only: bool = typer.Option(True, "--safe-only/--all-fixers"),
    open_draft_pr: bool = typer.Option(False, "--open-draft-pr"),
    use_gitpilot: bool = typer.Option(False, "--use-gitpilot"),
    max_repos: int = typer.Option(0, "--max-repos", help="0 = no limit"),
) -> None:
    """Bulk repair across every repository in an organization."""

    settings = get_settings()
    if settings.github_org != org:
        settings = settings.model_copy(update={"github_org": org})
    repos = GitHubOrgDiscovery(settings).list_repositories()
    if max_repos:
        repos = repos[:max_repos]

    summary = []
    for repo in repos:
        console.print(f"\n[bold]==>[/bold] {repo.full_name}")
        try:
            repair_repo_cmd(  # type: ignore[misc]
                full_name=repo.full_name,
                safe_only=safe_only,
                open_draft_pr=open_draft_pr,
                use_gitpilot=use_gitpilot,
            )
            summary.append((repo.full_name, "ok"))
        except typer.Exit:
            summary.append((repo.full_name, "dispatch_skipped"))
        except Exception as exc:  # noqa: BLE001
            summary.append((repo.full_name, f"error:{exc}"))

    table = Table(title=f"repair-org {org} summary")
    table.add_column("Repository")
    table.add_column("Outcome")
    for name, outcome in summary:
        table.add_row(name, outcome)
    console.print(table)


@app.command("ready")
def ready_cmd() -> None:
    """Self-check: storage writable, settings loaded, SelfRepair reachable."""

    from matrix_codex.observability.metrics import readiness_probe

    settings = get_settings()
    status = readiness_probe(settings)
    console.print_json(data=status)
    raise typer.Exit(code=0 if status["ready"] else 1)


if __name__ == "__main__":
    app()
