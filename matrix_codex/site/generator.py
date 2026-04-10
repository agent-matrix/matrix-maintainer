from __future__ import annotations

import json
from pathlib import Path

from matrix_codex.models import RepoHealthReport
from matrix_codex.reporting.incident_builder import incidents_from_reports
from matrix_codex.reporting.status_builder import build_summary, export_repos_json, export_summary_json
from matrix_codex.settings import Settings


def _read_reports(path: Path) -> list[RepoHealthReport]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [RepoHealthReport.model_validate(item) for item in payload.get("items", [])]


def generate_site(settings: Settings) -> None:
    data_dir = settings.status_site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    reports = _read_reports(settings.state_dir / "latest_status.json")
    summary = build_summary(settings.site_title, settings.site_description, reports)

    export_summary_json(data_dir / "summary.json", summary)
    export_repos_json(data_dir / "repos.json", reports)

    incidents = incidents_from_reports(reports)
    (data_dir / "incidents.json").write_text(
        json.dumps({"items": [incident.model_dump(mode="json") for incident in incidents]}, indent=2),
        encoding="utf-8",
    )
