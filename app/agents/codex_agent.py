from pathlib import Path

from app.agents.base import Agent
from app.execution.repo_executor import RepoExecutor


class CodexAgent(Agent):
    def __init__(self, executor: RepoExecutor | None = None) -> None:
        self.executor = executor or RepoExecutor()

    def run(self, task: dict[str, str]) -> dict[str, str | int]:
        repo_path = Path(task["repo_path"])
        issue = task.get("issue", "general-maintenance")

        for attempt in range(1, 4):
            result = self.executor.validate(repo_path)
            if result["status"] == "success":
                return {"status": "success", "attempt": attempt, "issue": issue}

        return {"status": "failed", "attempt": 3, "issue": issue}
