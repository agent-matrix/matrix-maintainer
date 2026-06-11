"""Standalone daily maintenance submitter (lightweight: httpx + pyyaml only).

Reads the maintainer inventory (config/repos.yml) and submits a dry-run
maintenance request per repo to SelfRepair's control-plane intake
(``POST /v1/plans``). SelfRepair records each request (inbox + notification),
runs the health check, and surfaces the result in its console.

Designed to run in CI without installing the full matrix-maintainer package:
only ``pip install httpx pyyaml`` is required. Reuses
``matrix_codex.control_plane`` (which imports only httpx).

Environment:
  SELFREPAIR_BASE_URL      default https://ruslanmv-selfrepair.hf.space
  SELFREPAIR_INGEST_TOKEN  required — least-privilege ingest service token
  MATRIX_CODEX_CLIENT_ID   default "matrix-maintainer"
  MM_REPOS_FILE            default config/repos.yml
  MM_MODE                  default dry_run
"""
from __future__ import annotations

import os
import pathlib
import sys

import yaml

# Make matrix_codex importable when run as a plain script in CI.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from matrix_codex.control_plane import submit_maintenance_request  # noqa: E402


def load_repos(path: str) -> list[dict]:
    data = yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8")) or {}
    return data.get("repositories", []) or []


def main() -> int:
    repos_file = os.environ.get("MM_REPOS_FILE", "config/repos.yml")
    mode = os.environ.get("MM_MODE", "dry_run")
    # Optional pilot filter: comma-separated repo names to include exclusively.
    only = {s.strip() for s in os.environ.get("MM_ONLY", "").split(",") if s.strip()}
    repos = load_repos(repos_file)
    if only:
        repos = [r for r in repos if r.get("name") in only]
    if not repos:
        print(f"No repositories found in {repos_file}" + (f" matching {only}" if only else ""))
        return 0

    failures = 0
    for item in repos:
        name = item.get("name")
        if not name:
            continue
        branch = item.get("default_branch", "main")
        try:
            res = submit_maintenance_request(name, branch=branch, mode=mode)
            print(f"submitted {name}: job={res.get('job_id')} status={res.get('status')}")
        except Exception as exc:  # keep going for the rest of the fleet
            failures += 1
            print(f"FAILED {name}: {exc}", file=sys.stderr)

    print(f"Done. {len(repos) - failures}/{len(repos)} submitted, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
