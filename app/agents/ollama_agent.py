from app.agents.base import Agent


class OllamaAgent(Agent):
    def run(self, task: dict[str, str]) -> dict[str, str]:
        return {
            "status": "not_implemented",
            "message": "Ollama strategy placeholder for local model execution",
            "repo": task.get("repo", ""),
        }
