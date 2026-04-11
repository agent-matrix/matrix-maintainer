from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from matrix_codex.models import utc_now


class RunRecord(BaseModel):
    run_id: str
    repo: str
    status: str
    operation: str
    created_at: str = Field(default_factory=utc_now)


class TaskRecord(BaseModel):
    task_id: str
    run_id: str
    repo: str
    task_type: str
    status: str
    risk_level: str
    created_at: str = Field(default_factory=utc_now)


class ExecutionRecord(BaseModel):
    execution_id: str
    task_id: str
    status: str
    summary: str = ""
    created_at: str = Field(default_factory=utc_now)


class PullRequestRecord(BaseModel):
    pr_id: str
    repo: str
    run_id: str
    url: str
    status: str
    created_at: str = Field(default_factory=utc_now)


class EventRecord(BaseModel):
    event_id: str
    run_id: str
    repo: str
    status: str
    payload: dict[str, object] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)


class HealthScanRecord(BaseModel):
    scan_id: str
    repo: str
    issue_type: str
    severity: str
    details: str
    created_at: str = Field(default_factory=utc_now)


class StorageDB:
    def __init__(self, path: Path) -> None:
        self.path = path
        if not self.path.exists():
            self.path.write_text('{"runs": [], "tasks": [], "executions": [], "pull_requests": [], "events": [], "health_scans": []}', encoding="utf-8")

    def _read(self) -> dict[str, list[dict[str, object]]]:
        import json

        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, list[dict[str, object]]]) -> None:
        import json

        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def append(self, key: str, model: BaseModel) -> None:
        data = self._read()
        data.setdefault(key, []).append(model.model_dump(mode="json"))
        self._write(data)

    def list(self, key: str) -> list[dict[str, object]]:
        return self._read().get(key, [])
