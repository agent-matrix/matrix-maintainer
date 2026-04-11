from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from matrix_codex.storage.models import EventRecord, StorageDB
from matrix_codex.utils.paths import repo_root

router = APIRouter(prefix="/maintainer", tags=["maintainer"])
storage = StorageDB(repo_root() / "state" / "maintainer_records.json")


class EventInput(BaseModel):
    run_id: str = Field(min_length=1)
    repo: str = Field(min_length=1)
    status: str = Field(min_length=1)
    payload: dict[str, object] = Field(default_factory=dict)


@router.get("/runs")
def list_runs() -> list[dict[str, object]]:
    return storage.list("runs")


@router.get("/tasks")
def list_tasks() -> list[dict[str, object]]:
    return storage.list("tasks")


@router.get("/events")
def list_events() -> list[dict[str, object]]:
    return storage.list("events")


@router.get("/health_scans")
def list_health_scans() -> list[dict[str, object]]:
    return storage.list("health_scans")


@router.post("/event")
def push_event(event: EventInput) -> dict[str, str]:
    from uuid import uuid4

    storage.append(
        "events",
        EventRecord(
            event_id=str(uuid4()),
            run_id=event.run_id,
            repo=event.repo,
            status=event.status,
            payload=event.payload,
        ),
    )
    return {"status": "ok"}
