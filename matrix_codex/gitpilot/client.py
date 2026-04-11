from __future__ import annotations

import json
import shutil
import subprocess

from matrix_codex.settings import Settings


class GitPilotClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def available(self) -> bool:
        return self.settings.gitpilot_enabled and shutil.which(self.settings.gitpilot_bin) is not None

    def run_headless(
        self,
        repo_full_name: str,
        message: str,
        branch: str | None = None,
        mode: str = "auto",
        output_format: str = "json",
    ) -> dict[str, object]:
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
            "--mode",
            mode,
            "--output",
            output_format,
        ]
        if self.settings.gitpilot_provider:
            command.extend(["--provider", self.settings.gitpilot_provider])
        if self.settings.gitpilot_message_model:
            command.extend(["--model", self.settings.gitpilot_message_model])
        if branch:
            command.extend(["-b", branch])

        proc = subprocess.run(command, capture_output=True, text=True)
        stdout = proc.stdout.strip()
        try:
            parsed = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            parsed = {
                "summary": stdout,
                "stderr": proc.stderr,
            }

        return {
            "success": proc.returncode == 0,
            "diff": parsed.get("diff", ""),
            "tests": parsed.get("tests", []),
            "summary": parsed.get("summary", stdout),
            "pr_message": parsed.get("pr_message", ""),
            "duration_seconds": parsed.get("duration_seconds", 0.0),
            "raw": parsed,
        }
