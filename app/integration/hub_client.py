from pathlib import Path

import yaml


class HubClient:
    def __init__(self, repos_path: Path = Path("config/repos.yml")) -> None:
        self.repos_path = repos_path

    def discover_repos(self) -> list[str]:
        if not self.repos_path.exists():
            return []

        payload = yaml.safe_load(self.repos_path.read_text()) or {}
        repos = payload.get("repositories", [])
        return [item["name"] for item in repos if isinstance(item, dict) and "name" in item]
