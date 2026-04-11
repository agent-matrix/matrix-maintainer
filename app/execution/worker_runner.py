from app.agents.base import Agent


class WorkerRunner:
    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def execute(self, task: dict[str, str]) -> dict[str, str | int]:
        return self.agent.run(task)
