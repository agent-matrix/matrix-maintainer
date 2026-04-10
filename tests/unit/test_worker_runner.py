from pathlib import Path

from matrix_codex.execution.worker_runner import detect_profile


def test_detect_profile_python(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    assert detect_profile(tmp_path) == "python-service"
