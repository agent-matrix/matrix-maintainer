"""Aggregate org-level report writer.

Writes a single JSON file under ``state/`` that captures the result of
a bulk scan or repair pass so other systems (status site, MatrixHub
badge publisher, humans grepping logs) can consume it without replaying
the event log.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from matrix_codex.selfrepair.dto import JsonReportDTO, RepoHealthReportDTO, SCHEMA_VERSION


def _slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_org_scan(
    state_dir: Path,
    org: str,
    health_reports: Iterable[RepoHealthReportDTO],
) -> Path:
    """Write a scan-org-<org>-<ts>.json file. Returns the path."""

    state_dir.mkdir(parents=True, exist_ok=True)
    items = [r.model_dump(mode="json") for r in health_reports]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "kind": "scan-org",
        "org": org,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "total": len(items),
            "healthy": sum(1 for it in items if it.get("status") == "healthy"),
            "degraded": sum(1 for it in items if it.get("status") == "degraded"),
            "down": sum(1 for it in items if it.get("status") == "down"),
            "unknown": sum(1 for it in items if it.get("status") == "unknown"),
        },
        "items": items,
    }
    out = state_dir / f"scan-org-{org}-{_slug()}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    # Also refresh the "latest" pointer for easy consumption.
    (state_dir / f"scan-org-{org}-latest.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return out


def write_repair(
    state_dir: Path,
    report: JsonReportDTO,
) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    safe_name = report.repo.replace("/", "__")
    out = state_dir / f"repair-{safe_name}-{_slug()}.json"
    out.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")
    return out
