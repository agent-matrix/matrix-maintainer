from pathlib import Path

def ensure_python311(pyproject_path: Path) -> bool:
    if not pyproject_path.exists():
        return False
    text = pyproject_path.read_text(encoding="utf-8")
    return (
        ">=3.11" in text
        or 'python_version = "3.11"' in text
        or 'requires-python = ">=3.11' in text
    )
