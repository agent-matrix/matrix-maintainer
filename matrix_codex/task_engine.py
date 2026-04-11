from __future__ import annotations

from pathlib import Path

import yaml

from matrix_codex.models import HealthIssue, MaintenanceTask


ISSUE_TO_TASK = {
    "ci_missing_recent_success": "repair_ci",
    "dependency_review_due": "update_dependencies",
    "lint_failure": "repair_lint",
    "tests_failing": "repair_tests",
}


def create_tasks(issues: list[HealthIssue], tasks_config_path: Path) -> list[MaintenanceTask]:
    payload = yaml.safe_load(tasks_config_path.read_text(encoding="utf-8")) or {}
    repo_overrides = payload.get("repositories", {})

    tasks: list[MaintenanceTask] = []
    for issue in issues:
        task_type = ISSUE_TO_TASK.get(issue.issue_type, "investigate")
        config = repo_overrides.get(issue.repo, {})
        allowed_paths = config.get("allowed_paths", ["tests/**", "pyproject.toml", "requirements*.txt"])
        tasks.append(
            MaintenanceTask(
                repo=issue.repo,
                issue_type=issue.issue_type,
                task_type=task_type,
                risk_level="high" if issue.severity in {"high", "critical"} else "medium",
                allowed_paths=allowed_paths,
                metadata={"issue_details": issue.details, "severity": issue.severity},
            )
        )
    return tasks
