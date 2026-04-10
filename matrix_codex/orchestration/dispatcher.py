from __future__ import annotations

from dataclasses import dataclass

import httpx

from matrix_codex.settings import Settings


@dataclass
class DispatchResult:
    ok: bool
    worker_url: str | None = None
    error: str | None = None


def dispatch_worker_workflow(*, settings: Settings, repo_full_name: str, operation: str, controller_run_id: str | None = None) -> DispatchResult:
    if not settings.github_token:
        return DispatchResult(ok=False, error="missing_github_token")

    url = f"https://api.github.com/repos/{repo_full_name}/actions/workflows/matrix-codex-worker.yml/dispatches"
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "ref": settings.github_base_branch,
        "inputs": {
            "operation": operation,
            "controller_run_id": controller_run_id or "",
            "base_branch": settings.github_base_branch,
        },
    }
    resp = httpx.post(url, headers=headers, json=payload, timeout=30.0)
    if resp.status_code in {200, 201, 204}:
        return DispatchResult(ok=True, worker_url=f"https://github.com/{repo_full_name}/actions")
    return DispatchResult(ok=False, error=f"dispatch_failed:{resp.status_code}")
