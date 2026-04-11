from abc import ABC, abstractmethod
from typing import Any


class Agent(ABC):
    @abstractmethod
    def run(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a maintenance task and return outcome metadata."""
