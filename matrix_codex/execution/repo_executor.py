from __future__ import annotations

import subprocess
from pathlib import Path


class ProfileRepoExecutor:
    def __init__(self, profile: dict[str, object]) -> None:
        self.profile = profile

    def run_install(self, repo_path: Path) -> int:
        cmd = self.profile.get("install", "python -m pip install -r requirements.txt")
        return subprocess.run(str(cmd), shell=True, cwd=repo_path, check=False).returncode

    def run_tests(self, repo_path: Path) -> int:
        cmd = self.profile.get("test", "pytest")
        return subprocess.run(str(cmd), shell=True, cwd=repo_path, check=False).returncode

    def run_lint(self, repo_path: Path) -> int:
        cmd = self.profile.get("lint", "python -m pip --version")
        return subprocess.run(str(cmd), shell=True, cwd=repo_path, check=False).returncode
