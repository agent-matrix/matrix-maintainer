from app.integration.hub_client import HubClient


class Inventory:
    def __init__(self, hub_client: HubClient | None = None) -> None:
        self.hub_client = hub_client or HubClient()

    def discover(self) -> list[str]:
        return self.hub_client.discover_repos()
