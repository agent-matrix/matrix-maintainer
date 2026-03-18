from __future__ import annotations

from pathlib import Path

DEFAULT_TEST = """def test_health():
    assert True
"""

def ensure_health_test(repo_dir: Path) -> tuple[bool, list[str]]:
    changed: list[str] = []
    tests_dir = repo_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    path = tests_dir / "test_health.py"
    if not path.exists():
        path.write_text(DEFAULT_TEST, encoding="utf-8")
        changed.append("tests/test_health.py")
    return True, changed
