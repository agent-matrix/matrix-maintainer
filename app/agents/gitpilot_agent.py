from app.agents.base import Agent


class GitPilotAgent(Agent):
    def run(self, task: dict[str, str]) -> dict[str, str]:
        return {
            "status": "not_implemented",
            "message": "GitPilot execution hook pending integration",
            "repo": task.get("repo", ""),
        }
