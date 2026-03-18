from __future__ import annotations

import shutil
from pathlib import Path

from git import Repo

from matrix_maintainer.models import RepoRef
from matrix_maintainer.settings import Settings
from matrix_maintainer.utils.paths import safe_repo_dir


class SandboxManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def clone_repo(self, repo: RepoRef) -> Path:
        target = safe_repo_dir(self.settings.work_dir, repo.full_name)
        if target.exists():
            shutil.rmtree(target)
        Repo.clone_from(repo.clone_url, target)
        return target
