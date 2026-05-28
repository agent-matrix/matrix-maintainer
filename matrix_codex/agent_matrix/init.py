from __future__ import annotations

import json
import logging

from matrix_codex.llm import OllaBridgeError, OllaBridgeUnavailable, get_llm_client
from matrix_codex.models import MaintenanceTask

logger = logging.getLogger(__name__)


_PLANNER_SYSTEM_PROMPT = (
    "You are the Matrix-AI planner. Produce a concise JSON plan for a "
    "single repository maintenance task. Output ONLY a JSON object with "
    "keys: repo (string), task_type (string), steps (array of strings, "
    "max 6). No prose, no markdown."
)


def _stub_plan(task: MaintenanceTask) -> dict[str, object]:
    return {
        "repo": task.repo,
        "task_type": task.task_type,
        "steps": [
            "analyze repository failure signals",
            "apply constrained patch",
            "execute validation commands",
        ],
    }


def get_plan_from_matrix_ai(task: MaintenanceTask) -> dict[str, object]:
    """Return a structured plan for the task.

    Uses OllaBridge Cloud when configured; otherwise returns a
    deterministic stub so offline / CI runs are unaffected.
    """

    client = get_llm_client()
    if not client.configured:
        return _stub_plan(task)

    user_payload = {
        "repo": task.repo,
        "issue_type": task.issue_type,
        "task_type": task.task_type,
        "risk_level": task.risk_level,
        "allowed_paths": task.allowed_paths,
        "metadata": task.metadata,
    }
    try:
        resp = client.chat(
            [
                {"role": "system", "content": _PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            temperature=0.2,
            max_tokens=512,
        )
    except (OllaBridgeUnavailable, OllaBridgeError) as exc:
        logger.warning("matrix_ai_planner_fallback: %s", exc)
        return _stub_plan(task)

    try:
        plan = json.loads(resp.content)
    except json.JSONDecodeError:
        logger.warning("matrix_ai_planner_non_json_response")
        return _stub_plan(task)

    # Validate the planner stayed within the schema we asked for.
    if not isinstance(plan, dict) or "repo" not in plan or "steps" not in plan:
        return _stub_plan(task)
    if not isinstance(plan.get("steps"), list):
        plan["steps"] = _stub_plan(task)["steps"]
    plan.setdefault("task_type", task.task_type)
    plan.setdefault("repo", task.repo)
    return plan


def check_guardian_approval(task: MaintenanceTask, max_files: int = 10) -> bool:
    if task.risk_level == "high":
        return False
    return task.metadata.get("files_changed", 0) <= max_files


def check_budget(task: MaintenanceTask, available_mxu: float) -> bool:
    estimated = float(task.metadata.get("estimated_cost_mxu", 0.2))
    return estimated <= available_mxu


def publish_event_to_hub(event: dict[str, object]) -> dict[str, object]:
    return {"status": "recorded", "event": event}
