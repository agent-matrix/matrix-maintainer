from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from matrix_codex.settings import Settings


class GitPilotClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def available(self) -> bool:
        return self.settings.gitpilot_enabled and shutil.which(self.settings.gitpilot_bin) is not None

    def run_headless(self, repo_full_name: str, message: str, branch: str | None = None) -> dict:
        if not self.available():
            return {"success": False, "error": "gitpilot unavailable", "output": ""}

        command = [
            self.settings.gitpilot_bin,
            "run",
            "-r",
            repo_full_name,
            "-m",
            message,
            "--headless",
        ]
        if branch:
            command.extend(["-b", branch])

        proc = subprocess.run(command, capture_output=True, text=True)
        stdout = proc.stdout.strip()
        try:
            return json.loads(stdout) if stdout else {"success": proc.returncode == 0, "output": stdout}
        except json.JSONDecodeError:
            return {
                "success": proc.returncode == 0,
                "output": stdout,
                "stderr": proc.stderr,
            }
