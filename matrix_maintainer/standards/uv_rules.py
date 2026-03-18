from pathlib import Path

def ensure_uv(pyproject_path: Path) -> bool:
    if not pyproject_path.exists():
        return False
    text = pyproject_path.read_text(encoding="utf-8").lower()
    return "[tool.uv]" in text or "uv sync" in text or "uv pip install" in text
