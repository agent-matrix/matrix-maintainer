from __future__ import annotations

import os
from pathlib import Path

from matrix_codex.execution.profile_runner import run_profile


def detect_profile(repo_dir: Path) -> str:
    config_path = repo_dir / "matrix-codex.yml"
    if config_path.exists():
        import yaml

        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if data.get("profile"):
            return str(data["profile"])

    if (repo_dir / "package.json").exists():
        return "node-web"
    if (repo_dir / "pyproject.toml").exists() or (repo_dir / "requirements.txt").exists():
        return "python-service"
    return "infra"


def main() -> int:
    repo_dir = Path(os.getenv("MATRIX_CODEX_REPO_DIR", ".")).resolve()
    profile = os.getenv("MATRIX_CODEX_PROFILE") or detect_profile(repo_dir)
    profiles_path = Path(os.getenv("MATRIX_CODEX_PROFILES_PATH", ".github/matrix-codex/profiles.yml"))

    run_profile(profile, repo_dir, profiles_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
