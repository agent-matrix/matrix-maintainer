from __future__ import annotations

from matrix_codex.settings import Settings
from matrix_codex.storage.models import StorageDB


def build_maintainer_status(settings: Settings) -> dict[str, object]:
    db = StorageDB(settings.state_dir / "maintainer_records.json")
    return {
        "runs": db.list("runs"),
        "tasks": db.list("tasks"),
        "events": db.list("events"),
        "health_scans": db.list("health_scans"),
        "pull_requests": db.list("pull_requests"),
    }
