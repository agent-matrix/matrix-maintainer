from pathlib import Path

from matrix_codex.models import HealthIssue
from matrix_codex.task_engine import create_tasks


def test_task_engine_maps_issue_to_task(tmp_path: Path) -> None:
    cfg = tmp_path / "tasks.yml"
    cfg.write_text("repositories: {}\n", encoding="utf-8")
    issues = [
        HealthIssue(
            repo="agent-matrix/repo-a",
            issue_type="tests_failing",
            details="unit test failure",
            severity="high",
        )
    ]

    tasks = create_tasks(issues, cfg)

    assert tasks[0].task_type == "repair_tests"
    assert tasks[0].risk_level == "high"
