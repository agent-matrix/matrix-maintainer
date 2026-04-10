from matrix_codex.inventory.org_discovery import GitHubOrgDiscovery
from matrix_codex.settings import get_settings
from matrix_codex.inventory.repo_inventory import save_inventory

if __name__ == "__main__":
    settings = get_settings()
    discovery = GitHubOrgDiscovery(settings)
    repos = discovery.list_repositories()
    save_inventory(settings, repos)
