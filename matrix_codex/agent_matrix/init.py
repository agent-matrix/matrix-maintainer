from __future__ import annotations

from matrix_codex.models import MaintenanceTask


def get_plan_from_matrix_ai(task: MaintenanceTask) -> dict[str, object]:
    return {
        "repo": task.repo,
        "task_type": task.task_type,
        "steps": [
            "analyze repository failure signals",
            "apply constrained patch",
            "execute validation commands",
        ],
    }


def check_guardian_approval(task: MaintenanceTask, max_files: int = 10) -> bool:
    if task.risk_level == "high":
        return False
    return task.metadata.get("files_changed", 0) <= max_files


def check_budget(task: MaintenanceTask, available_mxu: float) -> bool:
    estimated = float(task.metadata.get("estimated_cost_mxu", 0.2))
    return estimated <= available_mxu


def publish_event_to_hub(event: dict[str, object]) -> dict[str, object]:
    return {"status": "recorded", "event": event}
