"""Repair an MCP server. Tries SelfRepair safe-only first; escalates
to GitPilot only when the SelfRepair result explicitly asks for it.
"""

from __future__ import annotations

from typing import Any

from matrix_codex.mcp.manifest import MCPManifest
from matrix_codex.selfrepair import SelfRepairClient
from matrix_codex.selfrepair.dto import RepairResultDTO, RepoRefDTO


def _ref_from(manifest: MCPManifest) -> RepoRefDTO:
    return RepoRefDTO(
        full_name=str(manifest.source.repo).rstrip("/").split("github.com/", 1)[-1],
        clone_url=str(manifest.source.repo),
    )


def repair(
    manifest: MCPManifest,
    client: SelfRepairClient,
    *,
    use_gitpilot: bool = False,
) -> tuple[MCPManifest, RepairResultDTO, dict[str, Any]]:
    """Returns (updated manifest, repair result, audit record)."""

    ref = _ref_from(manifest)
    health = client.scan(ref)
    safe_result = client.repair(ref, health.issues, safe_only=True)

    audit: dict[str, Any] = {
        "engine": "selfrepair-safe",
        "applied": list(safe_result.applied),
        "skipped": list(safe_result.skipped),
        "failed": list(safe_result.failed),
        "escalated": False,
    }

    final = safe_result
    if safe_result.needs_escalation and use_gitpilot:
        # GitPilot escalation: invoke GitPilotRunner via existing engine.
        from matrix_codex.gitpilot.runner import GitPilotRunner
        from matrix_codex.models import MaintenanceTask
        from matrix_codex.settings import get_settings

        runner = GitPilotRunner(get_settings())
        task = MaintenanceTask(
            repo=ref.full_name,
            issue_type="mcp_repair_escalation",
            task_type="repair_gitpilot",
            risk_level="medium",
        )
        exec_result = runner.run_task(task)
        audit["engine"] = "gitpilot"
        audit["escalated"] = True
        audit["gitpilot_exit"] = exec_result.return_code
        # We don't have a structured RepairResultDTO from GitPilot today;
        # propagate the headline and let the publisher attach the audit.
        final = RepairResultDTO(
            repo=ref.full_name,
            applied=list(safe_result.applied),
            skipped=list(safe_result.skipped),
            failed=list(safe_result.failed),
            needs_escalation=False,
            escalation_reason=None,
            metadata={"gitpilot_summary": exec_result.stdout[:2000]},
        )

    if "selfrepair-scanned" not in manifest.tags.maintenance:
        manifest.tags.maintenance.append("selfrepair-scanned")
    if audit["escalated"] and "gitpilot-reviewed" not in manifest.tags.maintenance:
        manifest.tags.maintenance.append("gitpilot-reviewed")
    manifest.touch()
    return manifest, final, audit
