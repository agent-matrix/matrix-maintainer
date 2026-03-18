from __future__ import annotations

import json

from matrix_maintainer.models import RepoHealthReport, SiteSummary
from matrix_maintainer.reporting.repo_status import to_repo_item


def build_summary(title: str, description: str, reports: list[RepoHealthReport]) -> SiteSummary:
    summary = SiteSummary(title=title, description=description)
    for report in reports:
        summary.__dict__[report.status] = summary.__dict__.get(report.status, 0) + 1
    return summary


def export_summary_json(path, summary: SiteSummary) -> None:
    path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")


def export_repos_json(path, reports: list[RepoHealthReport]) -> None:
    payload = {"items": [to_repo_item(report) for report in reports]}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
