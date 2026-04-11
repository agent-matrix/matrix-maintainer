from matrix_codex.gitpilot.runner import GitPilotRunner
from matrix_codex.models import MaintenanceTask
from matrix_codex.settings import Settings


class DummyClient:
    def __init__(self) -> None:
        self.calls = 0

    def run_headless(self, **_: object) -> dict[str, object]:
        self.calls += 1
        if self.calls < 2:
            return {"success": False}
        return {"success": True, "summary": "patched", "duration_seconds": 1.2}


def test_gitpilot_runner_retries_until_success() -> None:
    runner = GitPilotRunner(Settings())
    runner.client = DummyClient()  # type: ignore[assignment]

    task = MaintenanceTask(repo="agent-matrix/repo-a", issue_type="tests_failing", task_type="repair_tests")
    result = runner.run_task(task)

    assert result.ok
    assert "patched" in result.stdout
