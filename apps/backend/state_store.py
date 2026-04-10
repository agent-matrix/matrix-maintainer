from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATE_PATH = Path("state/runtime_status.json")


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"repos": {}, "actions": []}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
