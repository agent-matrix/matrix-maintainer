"""GitPilot maintenance-agent adapter.

GitPilot is the default AI coder for the Agent-Matrix ecosystem: it is the
only component that *writes* patches. This adapter calls GitPilot's HTTP
``/repair`` endpoint (dry-run by default) and normalizes the response into a
maintenance outcome dict.

GitPilot reaches inference models only via OllaBridge on its own side; this
adapter never reads ``HF_TOKEN`` and never opens a real PR.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from app.agents.base import Agent

DEFAULT_GITPILOT_URL = "http://localhost:9000"

# Fail-closed forbidden globs supplied by default on minimal plans.
DEFAULT_FORBIDDEN_PATHS: list[str] = [
    ".env",
    "secrets/**",
    "**/*token*",
    "**/*secret*",
]


class GitPilotAgent(Agent):
    """Adapter that delegates patch generation to a GitPilot HTTP server."""

    def __init__(self, base_url: str | None = None, *, timeout: float = 60.0) -> None:
        self.base_url = (
            base_url or os.getenv("GITPILOT_URL", DEFAULT_GITPILOT_URL)
        ).rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------ #
    def run(self, task: dict[str, Any]) -> dict[str, Any]:
        plan = self._build_plan(task)
        repo = plan.get("repo_url", "")
        task_id = plan.get("task_id", "")

        try:
            resp = httpx.post(
                f"{self.base_url}/repair",
                json=plan,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
        except httpx.HTTPStatusError as exc:
            # Server responded but with an error status — surface it, don't raise.
            return {
                "status": "error",
                "repo": repo,
                "task_id": task_id,
                "message": "GitPilot returned an error response",
                "error": f"http {exc.response.status_code}",
            }
        except Exception as exc:  # connection / timeout / parse — graceful
            return {
                "status": "unavailable",
                "repo": repo,
                "task_id": task_id,
                "message": "GitPilot unreachable",
                "error": str(exc),
            }

        return self._normalize(payload, repo=repo, task_id=task_id)

    # ------------------------------------------------------------------ #
    def _build_plan(self, task: dict[str, Any]) -> dict[str, Any]:
        """Use a full ``plan`` if provided, else build a minimal dry-run plan."""
        if isinstance(task.get("plan"), dict):
            plan = dict(task["plan"])
            plan.setdefault("mode", "dry_run")
            return plan

        repo_url = task.get("repo_url") or task.get("repo") or ""
        task_id = task.get("task_id") or "matrix-maintainer-repair"
        issues = list(task.get("issues", []) or [])
        allowed_paths = list(task.get("allowed_paths", []) or [])

        return {
            "client_id": task.get("client_id", "matrix-maintainer"),
            "workspace_id": task.get("workspace_id", "matrix-maintainer-ws"),
            "task_id": task_id,
            "repo_url": repo_url,
            "branch": task.get("branch", "main"),
            "mode": "dry_run",
            "issues": issues,
            "allowed_paths": allowed_paths,
            "forbidden_paths": list(
                task.get("forbidden_paths", DEFAULT_FORBIDDEN_PATHS)
            ),
            "coder": {
                "provider": task.get("coder_provider", "gitpilot"),
                "model": task.get("coder_model", "code-coder"),
            },
            "sandbox": {
                "provider": "matrixlab",
                "profile": "default",
                "required": bool(task.get("sandbox_required", False)),
            },
            "human_approval": bool(task.get("human_approval", False)),
        }

    @staticmethod
    def _normalize(
        payload: dict[str, Any], *, repo: str, task_id: str
    ) -> dict[str, Any]:
        """Normalize a GitPilot repair-response into a maintenance outcome."""
        if not isinstance(payload, dict):
            payload = {}

        raw_changed = payload.get("changed_files", []) or []
        changed_files: list[str] = []
        for item in raw_changed:
            if isinstance(item, str):
                changed_files.append(item)
            elif isinstance(item, dict) and isinstance(item.get("path"), str):
                changed_files.append(item["path"])

        return {
            "status": payload.get("status", "unknown"),
            "repo": repo,
            "task_id": payload.get("task_id", task_id),
            "patch_preview": payload.get("patch_preview", ""),
            "changed_files": changed_files,
            "review": payload.get("review", ""),
            "risk_level": payload.get("risk_level", "low"),
            "sandbox_result": payload.get("sandbox_result"),
            "pr_url": payload.get("pr_url"),
        }
