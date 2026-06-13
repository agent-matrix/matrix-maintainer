"""Submit maintenance requests to SelfRepair's control-plane intake.

Matrix-Maintainer is a *client* of SelfRepair, focused on the agent-matrix
organization. Rather than orchestrating repairs locally, it submits a
maintenance request per inventory repo to SelfRepair's ``POST /v1/plans``
endpoint. SelfRepair is the system of record: it records the request (inbox +
notification), runs the health check, and surfaces everything in its console.

Security:
* Authentication uses a least-privilege **ingest service token**
  (``SELFREPAIR_INGEST_TOKEN``) — it can only submit plans, not administer.
* This module never reads or transmits ``HF_TOKEN``. Only OllaBridge holds it.
* Requests default to ``dry_run``: SelfRepair will not open real PRs.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://ruslanmv-selfrepair.hf.space"


def base_url() -> str:
    return os.environ.get("SELFREPAIR_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def ingest_token() -> str | None:
    # SELFREPAIR_INGEST_TOKEN is the dedicated service secret; fall back to the
    # generic SELFREPAIR_API_KEY for convenience in mixed setups.
    return os.environ.get("SELFREPAIR_INGEST_TOKEN") or os.environ.get("SELFREPAIR_API_KEY")


def client_id() -> str:
    return os.environ.get("MATRIX_CODEX_CLIENT_ID", "matrix-maintainer")


def _daily_idempotency_key(repo_url: str, mode: str) -> str:
    day = _dt.date.today().isoformat()
    digest = hashlib.sha1(f"{repo_url}|{day}|{mode}".encode()).hexdigest()[:16]
    return f"mm-{digest}"


def to_repo_url(name_or_url: str) -> str:
    """Accept ``owner/name`` or a full URL and return a GitHub URL."""
    s = name_or_url.strip()
    if s.startswith("http://") or s.startswith("https://"):
        return s
    return f"https://github.com/{s}"


def submit_maintenance_request(
    repo: str,
    *,
    branch: str = "main",
    mode: str = "dry_run",
    requested_by: str = "daily-orchestrator",
    message: str = "Daily health check",
    idempotency_key: str | None = None,
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    """Submit one maintenance request. Returns SelfRepair's JSON response.

    Raises RuntimeError if no ingest token is configured, or httpx.HTTPError
    on transport/HTTP failures (callers should catch and continue per-repo).
    """
    token = ingest_token()
    if not token:
        raise RuntimeError(
            "SELFREPAIR_INGEST_TOKEN is not set; cannot submit to SelfRepair."
        )
    repo_url = to_repo_url(repo)
    body = {
        "client_id": client_id(),
        "type": "maintenance_request",
        "repo_url": repo_url,
        "branch": branch,
        "mode": mode,
        "requested_by": requested_by,
        "message": message,
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key or _daily_idempotency_key(repo_url, mode),
    }
    with httpx.Client(timeout=httpx.Timeout(timeout_seconds)) as c:
        resp = c.post(f"{base_url()}/v1/plans", json=body, headers=headers)
        resp.raise_for_status()
        return resp.json()
