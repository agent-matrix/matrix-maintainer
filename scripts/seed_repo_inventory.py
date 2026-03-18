from matrix_maintainer.inventory.org_discovery import GitHubOrgDiscovery
from matrix_maintainer.settings import get_settings
from matrix_maintainer.inventory.repo_inventory import save_inventory

if __name__ == "__main__":
    settings = get_settings()
    discovery = GitHubOrgDiscovery(settings)
    repos = discovery.list_repositories()
    save_inventory(settings, repos)
