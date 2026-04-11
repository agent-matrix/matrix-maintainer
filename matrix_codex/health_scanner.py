from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from matrix_codex.models import HealthIssue


@dataclass(slots=True)
class ScannerConfig:
    repositories_file: Path


class HealthScanner:
    """Detection engine for repo-level maintenance signals."""

    def __init__(self, config: ScannerConfig) -> None:
        self.config = config

    def scan(self) -> list[HealthIssue]:
        payload = yaml.safe_load(self.config.repositories_file.read_text(encoding="utf-8")) or {}
        issues: list[HealthIssue] = []
        for repo in payload.get("repositories", []):
            name = repo.get("name")
            if not name:
                continue
            if repo.get("run_tests", True):
                issues.append(
                    HealthIssue(
                        repo=name,
                        issue_type="ci_missing_recent_success",
                        details="No recent successful CI run found in cached scan.",
                        severity="medium",
                        metadata={"source": "scanner", "profile": repo.get("profile", "unknown")},
                    )
                )
            if repo.get("dependency_maintenance", True):
                issues.append(
                    HealthIssue(
                        repo=name,
                        issue_type="dependency_review_due",
                        details="Dependency maintenance window reached.",
                        severity="low",
                        metadata={"source": "scanner"},
                    )
                )
        return issues
