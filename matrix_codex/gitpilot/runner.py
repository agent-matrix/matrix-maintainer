from __future__ import annotations

from matrix_codex.gitpilot.client import GitPilotClient
from matrix_codex.models import ExecutionResult, MaintenanceTask
from matrix_codex.settings import Settings


class GitPilotRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = GitPilotClient(settings)

    def run_task(self, task: MaintenanceTask, retries: int = 2) -> ExecutionResult:
        message = f"{task.task_type} for {task.repo}: {task.issue_type}"
        for attempt in range(1, retries + 2):
            result = self.client.run_headless(
                repo_full_name=task.repo,
                message=message,
                mode=self.settings.gitpilot_mode,
                output_format="json",
            )
            if result.get("success"):
                return ExecutionResult(
                    command="gitpilot run",
                    return_code=0,
                    stdout=result.get("summary", "success"),
                    stderr="",
                    duration_seconds=float(result.get("duration_seconds", 0.0)),
                )
        return ExecutionResult(
            command="gitpilot run",
            return_code=1,
            stdout="",
            stderr="gitpilot failed after retries",
            duration_seconds=0.0,
        )
