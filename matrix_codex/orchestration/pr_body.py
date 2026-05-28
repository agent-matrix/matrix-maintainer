"""Shared PR-body template for orchestrator-opened pull requests.

Every PR that matrix-maintainer (or its workers) opens MUST include the
blocks rendered here so reviewers can see:

* what was scanned
* which issues were found
* which fixes were applied / skipped / failed
* the sandbox validation result
* the risk tier and approval rationale
* a footer with traceability ids

Do not invent ad-hoc PR bodies elsewhere -- use :func:`render`.
"""

from __future__ import annotations

from textwrap import dedent
from typing import Iterable

from matrix_codex.selfrepair.dto import (
    HealthIssueDTO,
    JsonReportDTO,
    RepairResultDTO,
    RepoHealthReportDTO,
    ValidationReportDTO,
)


_RISK_RATIONALE = {
    "low": (
        "Low-risk maintenance (formatting, README, metadata). Eligible for "
        "auto-draft PR; still requires human merge."
    ),
    "medium": (
        "Medium-risk maintenance (CI, dependencies, tests). Draft PR opens "
        "for review; merge requires a human approver."
    ),
    "high": (
        "High-risk change (auth, security, database, deploys). Plan-only by "
        "default. Explicit human approval required before any merge."
    ),
    "critical": (
        "Critical change. Halted before apply. A human owner must intervene."
    ),
}


def _bullet(lines: Iterable[str]) -> str:
    items = [f"- {ln}" for ln in lines if ln]
    return "\n".join(items) if items else "_none_"


def _render_health(h: RepoHealthReportDTO | None) -> str:
    if h is None:
        return "_no health data_"
    lines = [
        f"**Status**: `{h.status}`",
        f"**Issues found**: {len(h.issues)}",
    ]
    if h.issues:
        lines.append("")
        lines.append("<details><summary>Issue list</summary>\n")
        for issue in h.issues:
            lines.append(
                f"- `{issue.issue_type}` (severity: {issue.severity}) -- {issue.details}"
            )
        lines.append("\n</details>")
    return "\n".join(lines)


def _render_repair(r: RepairResultDTO | None) -> str:
    if r is None:
        return "_no repair attempted_"
    body = dedent(
        f"""
        **Applied**:
        {_bullet(r.applied)}

        **Skipped**:
        {_bullet(r.skipped)}

        **Failed**:
        {_bullet(r.failed)}

        **Changed files**:
        {_bullet(r.changed_files)}
        """
    ).strip()
    if r.needs_escalation:
        body += (
            f"\n\n> :warning: Needs escalation -- {r.escalation_reason or 'unspecified'}"
        )
    return body


def _render_validation(v: ValidationReportDTO | None) -> str:
    if v is None:
        return "_no validation run_"
    rows = [
        ("install", v.install_ok),
        ("test", v.test_ok),
        ("start", v.start_ok),
        ("health-test", v.health_test_ok),
    ]
    lines = [f"| {name} | {'OK' if ok else 'FAIL'} |" for name, ok in rows]
    table = "| Step | Result |\n|---|---|\n" + "\n".join(lines)
    return f"Sandbox: `{v.sandbox}`\n\n{table}"


def render(
    *,
    report: JsonReportDTO,
    risk_level: str = "medium",
    operation: str = "repair",
    controller_run_id: str | None = None,
    worker_run_url: str | None = None,
    use_gitpilot: bool = False,
) -> str:
    """Return the PR body for an orchestrator-opened pull request."""

    rationale = _RISK_RATIONALE.get(risk_level.lower(), _RISK_RATIONALE["medium"])
    body = dedent(
        f"""
        ## Matrix-Maintainer: `{operation}` on `{report.repo}`

        > Opened by the matrix-maintainer orchestrator. **Do not merge until
        > validations pass and a human reviewer has approved.**

        ### Risk tier: `{risk_level}`
        {rationale}

        ### Health
        {_render_health(report.health)}

        ### Repair actions
        Repair engine: {'GitPilot (LLM-assisted)' if use_gitpilot else 'SelfRepair (deterministic, safe-only)'}

        {_render_repair(report.repair)}

        ### Validation
        {_render_validation(report.validation)}

        ---

        <sub>
        controller_run_id: <code>{controller_run_id or 'n/a'}</code><br/>
        worker_run: {worker_run_url or '_pending_'}<br/>
        schema: <code>{report.schema_version}</code> -- generated {report.generated_at}
        </sub>
        """
    ).strip()
    return body + "\n"


def render_for_issues(
    *,
    repo_full_name: str,
    issues: list[HealthIssueDTO],
    risk_level: str = "medium",
) -> str:
    """Convenience wrapper for the report-only case (no repair yet)."""

    from matrix_codex.selfrepair.dto import RepoRefDTO

    health = RepoHealthReportDTO(
        repo=RepoRefDTO(full_name=repo_full_name, clone_url=f"https://github.com/{repo_full_name}.git"),
        status="degraded" if issues else "healthy",
        issues=issues,
    )
    report = JsonReportDTO(repo=repo_full_name, health=health)
    return render(report=report, risk_level=risk_level, operation="scan")
