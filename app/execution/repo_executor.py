from pathlib import Path
import subprocess


class RepoExecutor:
    def validate(self, repo_path: Path) -> dict[str, str]:
        try:
            subprocess.run(["pytest"], cwd=repo_path, check=True, capture_output=True, text=True)
            return {"status": "success"}
        except subprocess.CalledProcessError as exc:
            return {"status": "failed", "output": exc.stdout + exc.stderr}
