from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import yaml

WORKER_WORKFLOW = "matrix-codex-worker.yml"


def load_config(path: str) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _repo_name(item: str | dict[str, Any]) -> str:
    if isinstance(item, str):
        return item
    return str(item["name"])


def _repo_branch(item: str | dict[str, Any], default_branch: str) -> str:
    if isinstance(item, str):
        return default_branch
    return str(item.get("branch", default_branch))


def trigger_workflow(org: str, repo: str, operation: str, token: str, ref: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{org}/{repo}/actions/workflows/{WORKER_WORKFLOW}/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"ref": ref, "inputs": {"operation": operation}}
    response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
    return {
        "repo": f"{org}/{repo}",
        "workflow": WORKER_WORKFLOW,
        "status_code": response.status_code,
        "ok": response.status_code == 204,
        "response": response.text[:1000],
        "ref": ref,
        "operation": operation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Trigger matrix-codex worker workflow across repositories")
    parser.add_argument("--config", required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--target-repo", required=False)
    parser.add_argument("--delay-seconds", type=float, default=1.5)
    args = parser.parse_args()

    token = os.getenv("GH_TOKEN")
    if not token:
        print("GH_TOKEN is required", file=sys.stderr)
        return 1

    config = load_config(args.config)
    org = config["organization"]
    default_branch = config.get("default_branch", "main")
    repositories = config["repositories"]

    results: list[dict[str, Any]] = []
    for item in repositories:
        repo = _repo_name(item)
        if args.target_repo and repo != args.target_repo:
            continue
        ref = _repo_branch(item, default_branch)
        result = trigger_workflow(org, repo, args.operation, token, ref=ref)
        print(f"{result['repo']}: {'OK' if result['ok'] else 'FAILED'} ({result['status_code']})")
        results.append(result)
        time.sleep(args.delay_seconds)

    Path("orchestration-results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    failed = [r for r in results if not r["ok"]]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
