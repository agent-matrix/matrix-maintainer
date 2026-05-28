"""HTTP client for SelfRepair's `/v1/rpc` JSON-RPC surface.

The wire contract:

* POST ``{base_url}/v1/rpc`` with::

    {"jsonrpc": "2.0", "id": "<uuid>", "method": "<name>", "params": {...}}

* SelfRepair responds with::

    {"jsonrpc": "2.0", "id": "<uuid>", "result": {...}}
    {"jsonrpc": "2.0", "id": "<uuid>", "error": {"code": int, "message": str}}

Methods implemented here:

* ``selfrepair.scan``     -> RepoHealthReportDTO payload
* ``selfrepair.repair``   -> RepairResultDTO payload
* ``selfrepair.validate`` -> ValidationReportDTO payload
* ``selfrepair.report``   -> JsonReportDTO payload

Retries with exponential backoff. Never blocks the orchestrator on a
flaky SelfRepair instance for more than ``timeout_seconds``.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from matrix_codex.selfrepair.client import SelfRepairClient, SelfRepairError
from matrix_codex.selfrepair.dto import (
    HealthIssueDTO,
    JsonReportDTO,
    RepairResultDTO,
    RepoHealthReportDTO,
    RepoRefDTO,
    ValidationReportDTO,
)

logger = logging.getLogger(__name__)


class SelfRepairHttpClient(SelfRepairClient):
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 120.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._client = http_client or httpx.Client(timeout=httpx.Timeout(timeout_seconds))

    # ----- public API -----------------------------------------------------

    def scan(self, repo: RepoRefDTO, *, profile: str | None = None) -> RepoHealthReportDTO:
        params: dict[str, Any] = {"repo": repo.model_dump(mode="json")}
        if profile is not None:
            params["profile"] = profile
        data = self._rpc("selfrepair.scan", params)
        return RepoHealthReportDTO.model_validate(data)

    def repair(
        self,
        repo: RepoRefDTO,
        issues: list[HealthIssueDTO],
        *,
        safe_only: bool = True,
        branch: str | None = None,
    ) -> RepairResultDTO:
        data = self._rpc(
            "selfrepair.repair",
            {
                "repo": repo.model_dump(mode="json"),
                "issues": [i.model_dump(mode="json") for i in issues],
                "safe_only": safe_only,
                "branch": branch,
            },
        )
        return RepairResultDTO.model_validate(data)

    def validate(
        self,
        repo: RepoRefDTO,
        *,
        in_sandbox: bool = True,
    ) -> ValidationReportDTO:
        data = self._rpc(
            "selfrepair.validate",
            {"repo": repo.model_dump(mode="json"), "in_sandbox": in_sandbox},
        )
        return ValidationReportDTO.model_validate(data)

    def report(self, repo: RepoRefDTO) -> JsonReportDTO:
        data = self._rpc("selfrepair.report", {"repo": repo.model_dump(mode="json")})
        return JsonReportDTO.model_validate(data)

    # ----- transport ------------------------------------------------------

    @retry(
        reraise=True,
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
    )
    def _rpc(self, method: str, params: dict[str, Any]) -> Any:
        request_id = str(uuid.uuid4())
        body = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        url = f"{self._base_url}/v1/rpc"
        try:
            resp = self._client.post(url, json=body, headers=headers)
        except httpx.TransportError as exc:
            logger.warning("selfrepair_http_transport_error: %s", exc)
            raise
        if resp.status_code >= 500:
            resp.raise_for_status()
        if resp.status_code >= 400:
            raise SelfRepairError(f"selfrepair_http_{resp.status_code}: {resp.text[:500]}")
        payload = resp.json()
        if "error" in payload and payload["error"]:
            err = payload["error"]
            raise SelfRepairError(
                f"selfrepair_rpc_error code={err.get('code')} message={err.get('message')}"
            )
        return payload.get("result")

    def close(self) -> None:  # pragma: no cover - lifecycle
        self._client.close()
