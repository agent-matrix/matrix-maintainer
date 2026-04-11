import os

import httpx


class GitHubClient:
    def __init__(self) -> None:
        self.token = os.getenv("GITHUB_TOKEN") or os.getenv("CROSS_REPO_TOKEN", "")

    def trigger_workflow(self, repo: str, run_id: str, plan: dict[str, object]) -> None:
        if not self.token:
            return

        url = f"https://api.github.com/repos/{repo}/actions/workflows/maintainer.yml/dispatches"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
        }
        payload = {"ref": "main", "inputs": {"run_id": run_id, "plan": str(plan)}}
        httpx.post(url, headers=headers, json=payload, timeout=20.0)
