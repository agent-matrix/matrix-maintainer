from __future__ import annotations

from matrix_codex.models import RepoRef
from matrix_codex.settings import Settings


class GitHubOrgDiscovery:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        try:
            from github import Github
        except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional runtime deps
            raise RuntimeError("PyGithub is required for GitHub org discovery. Install dependencies with `make install`.") from exc
        self.client = Github(settings.github_token) if settings.github_token else Github()

    def list_repositories(self) -> list[RepoRef]:
        org = self.client.get_organization(self.settings.github_org)
        repos: list[RepoRef] = []
        for repo in org.get_repos():
            repos.append(
                RepoRef(
                    name=repo.name,
                    full_name=repo.full_name,
                    clone_url=repo.clone_url,
                    default_branch=repo.default_branch or self.settings.github_base_branch,
                    archived=repo.archived,
                    private=repo.private,
                )
            )
        return repos
