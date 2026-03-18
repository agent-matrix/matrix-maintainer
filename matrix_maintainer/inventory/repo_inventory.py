from __future__ import annotations

import json
from pathlib import Path

from matrix_maintainer.models import RepoRef
from matrix_maintainer.settings import Settings


def inventory_path(settings: Settings) -> Path:
    return settings.state_dir / "repo_inventory.json"


def save_inventory(settings: Settings, repos: list[RepoRef]) -> None:
    inventory_path(settings).write_text(
        json.dumps([repo.model_dump() for repo in repos], indent=2),
        encoding="utf-8",
    )


def load_inventory(settings: Settings) -> list[RepoRef]:
    path = inventory_path(settings)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [RepoRef.model_validate(item) for item in data]
