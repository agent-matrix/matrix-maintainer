from __future__ import annotations

import json
from pathlib import Path

from matrix_maintainer.models import RepoHealthReport
from matrix_maintainer.utils.clock import utc_timestamp


def write_history(path: Path, reports: list[RepoHealthReport]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": utc_timestamp(),
        "items": [r.model_dump(mode="json") for r in reports],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
