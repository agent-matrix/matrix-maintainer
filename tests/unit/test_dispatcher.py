from types import SimpleNamespace

from matrix_codex.orchestration.dispatcher import dispatch_worker_workflow
from matrix_codex.settings import Settings


def test_dispatch_uses_repo_branch_and_worker_workflow(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return SimpleNamespace(status_code=204)

    monkeypatch.setattr("matrix_codex.orchestration.dispatcher.httpx.post", fake_post)
    settings = Settings(
        GITHUB_TOKEN="token",
        GITHUB_BASE_BRANCH="main",
        WORKER_WORKFLOW_FILE="repo-maintenance-worker.yml",
    )

    result = dispatch_worker_workflow(
        settings=settings,
        repo_full_name="acme/repo",
        operation="daily-maintenance",
        base_branch="develop",
        controller_run_id="123",
    )

    assert result.ok is True
    assert captured["url"].endswith("/actions/workflows/repo-maintenance-worker.yml/dispatches")
    assert captured["json"]["ref"] == "develop"
    assert captured["json"]["inputs"]["base_branch"] == "develop"
