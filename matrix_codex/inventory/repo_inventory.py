from __future__ import annotations

import json
from pathlib import Path

from matrix_codex.models import RepoRef
from matrix_codex.settings import Settings


def inventory_path(settings: Settings) -> Path:
    return settings.state_dir / "repo_inventory.json"


def save_inventory(settings: Settings, repos: list[RepoRef]) -> None:
    path = inventory_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([repo.model_dump() for repo in repos], indent=2),
        encoding="utf-8",
    )


def load_inventory(settings: Settings) -> list[RepoRef]:
    path = inventory_path(settings)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [RepoRef.model_validate(item) for item in data]
