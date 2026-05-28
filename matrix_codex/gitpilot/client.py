from __future__ import annotations

import json
import logging
import shutil
import subprocess

from matrix_codex.llm import merged_subprocess_env
from matrix_codex.settings import Settings

logger = logging.getLogger(__name__)


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
        # GitPilot reads model from --model OR OLLABRIDGE_MODEL/OPENAI_*: inject
        # both via env (below) and pass --model when explicitly configured.
        if self.settings.gitpilot_message_model:
            command.extend(["--model", self.settings.gitpilot_message_model])
        elif self.settings.ollabridge_model:
            command.extend(["--model", self.settings.ollabridge_model])
        if branch:
            command.extend(["-b", branch])

        # Route GitPilot's LLM calls through OllaBridge by overriding the
        # OpenAI-compatible env. GitPilot already speaks OpenAI, so this is
        # transparent to it.
        env = merged_subprocess_env(self.settings)
        if not env.get("OPENAI_API_KEY"):
            logger.warning(
                "gitpilot_invoked_without_ollabridge_key",
                extra={"repo": repo_full_name},
            )

        proc = subprocess.run(command, capture_output=True, text=True, env=env)
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
