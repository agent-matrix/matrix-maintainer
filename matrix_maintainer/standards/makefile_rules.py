from __future__ import annotations

from pathlib import Path

DEFAULT_MAKEFILE = """.PHONY: install test start

install:
	uv sync

test:
	uv run pytest -q

start:
	uv run python -m app || uv run python -m src || python -c "print('start target placeholder')"
"""

def ensure_makefile(repo_dir: Path) -> tuple[bool, list[str]]:
    changed: list[str] = []
    makefile = repo_dir / "Makefile"
    if not makefile.exists():
        makefile.write_text(DEFAULT_MAKEFILE, encoding="utf-8")
        changed.append("Makefile")
        return True, changed

    text = makefile.read_text(encoding="utf-8")
    updated = text
    if "install:" not in updated:
        updated += "\ninstall:\n\tuv sync\n"
    if "test:" not in updated:
        updated += "\ntest:\n\tuv run pytest -q\n"
    if "start:" not in updated:
        updated += "\nstart:\n\tuv run python -m app || uv run python -m src || python -c \"print('start target placeholder')\"\n"
    if updated != text:
        makefile.write_text(updated, encoding="utf-8")
        changed.append("Makefile")
    return True, changed
