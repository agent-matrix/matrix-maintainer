"""Tests for the GitPilotAgent HTTP adapter."""

from __future__ import annotations

from typing import Any

import httpx

from app.agents.gitpilot_agent import GitPilotAgent

TASK: dict[str, Any] = {
    "repo_url": "https://github.com/agent-matrix/network.matrixhub",
    "task_id": "wire-test",
    "issues": [
        {
            "id": "missing-health-test",
            "severity": "medium",
            "description": "no health test",
            "recommended_action": "add tests/test_health.py",
        }
    ],
    "allowed_paths": ["tests/test_health.py"],
}


def test_run_unreachable_is_graceful(monkeypatch) -> None:
    def boom(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "post", boom)

    # Point at a definitely-unused port to be safe even without the monkeypatch.
    agent = GitPilotAgent(base_url="http://127.0.0.1:1")
    outcome = agent.run(TASK)

    assert outcome["status"] == "unavailable"
    assert outcome["repo"] == TASK["repo_url"]
    assert "error" in outcome
    # Never raises.


def test_run_normalizes_gitpilot_response(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url, json=None, headers=None, timeout=None):  # noqa: A002
        captured["url"] = url
        captured["json"] = json
        return httpx.Response(
            200,
            json={
                "task_id": "wire-test",
                "status": "ok",
                "mode": "dry_run",
                "risk_level": "low",
                "patch_preview": "--- a/tests/test_health.py\n+++ b/tests/test_health.py",
                "changed_files": [
                    {"path": "tests/test_health.py", "change_type": "added"}
                ],
                "review": "Adds a health smoke test. Risk: low.",
                "sandbox_result": None,
                "pr_url": None,
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    agent = GitPilotAgent(base_url="http://gitpilot.test")
    outcome = agent.run(TASK)

    # A minimal dry-run plan was built and posted to /repair.
    assert captured["url"] == "http://gitpilot.test/repair"
    assert captured["json"]["mode"] == "dry_run"
    assert captured["json"]["coder"]["provider"] == "gitpilot"
    assert captured["json"]["allowed_paths"] == ["tests/test_health.py"]
    assert captured["json"]["forbidden_paths"]  # defaults applied

    # Normalized outcome.
    assert outcome["status"] == "ok"
    assert outcome["repo"] == TASK["repo_url"]
    assert outcome["task_id"] == "wire-test"
    assert outcome["patch_preview"]
    assert outcome["changed_files"] == ["tests/test_health.py"]
    assert isinstance(outcome["review"], str)
    assert outcome["risk_level"] == "low"
    assert outcome["pr_url"] is None


def test_run_accepts_full_plan(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url, json=None, headers=None, timeout=None):  # noqa: A002
        captured["json"] = json
        return httpx.Response(
            200,
            json={"status": "blocked", "patch_preview": "", "changed_files": []},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    plan = {
        "client_id": "matrix-maintainer",
        "workspace_id": "ws-1",
        "task_id": "full-plan",
        "repo_url": "https://github.com/agent-matrix/x",
        "issues": [],
        "allowed_paths": [],
    }
    agent = GitPilotAgent(base_url="http://gitpilot.test")
    outcome = agent.run({"plan": plan})

    # The provided plan is used and forced to dry-run.
    assert captured["json"]["task_id"] == "full-plan"
    assert captured["json"]["mode"] == "dry_run"
    assert outcome["status"] == "blocked"
