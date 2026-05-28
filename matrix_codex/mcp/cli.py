"""`matrix-maintainer mcp ...` Typer subapp.

Registered onto the main app in :mod:`matrix_codex.cli` via
``app.add_typer(mcp_cli.app, name="mcp")``.
"""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from matrix_codex.mcp import discovery as _discovery
from matrix_codex.mcp import publisher as _publisher
from matrix_codex.mcp import repair as _repair
from matrix_codex.mcp import verify as _verify
from matrix_codex.mcp.license import decide as license_decide
from matrix_codex.selfrepair import get_client
from matrix_codex.settings import get_settings

app = typer.Typer(add_completion=False, help="MCP server maintenance (Surface B).", no_args_is_help=True)
console = Console()


@app.command("import")
def import_cmd(
    url: str = typer.Argument(..., help="Upstream repository URL (https://github.com/...)"),
    title: str | None = typer.Option(None, "--title"),
    summary: str | None = typer.Option(None, "--summary"),
    license_id: str | None = typer.Option(None, "--license", help="SPDX id, e.g. MIT, Apache-2.0"),
    capabilities: list[str] = typer.Option([], "--capability", help="Capability tag (repeatable)"),
) -> None:
    """Create a manifest skeleton for an upstream MCP server."""

    settings = get_settings()
    manifest, license_decision = _discovery.import_upstream(
        url,
        title=title,
        summary=summary,
        license_id=license_id,
        capabilities=capabilities or None,
    )
    path = _publisher.save(settings.mcp_state_dir, manifest)
    console.print_json(
        data={
            "manifest": manifest.model_dump(mode="json"),
            "license": {
                "spdx_id": license_decision.spdx_id,
                "policy_class": license_decision.policy_class,
                "allowed": license_decision.allowed,
                "reason": license_decision.reason,
            },
            "path": str(path),
        }
    )


@app.command("tag")
def tag_cmd(
    manifest_id: str = typer.Argument(...),
    capability: list[str] = typer.Option([], "--capability"),
    risk: list[str] = typer.Option([], "--risk"),
    quality: list[str] = typer.Option([], "--quality"),
) -> None:
    """Apply manual tags to an imported manifest."""

    settings = get_settings()
    manifest = _publisher.load(settings.mcp_state_dir, manifest_id)
    for c in capability:
        if c not in manifest.tags.capability:
            manifest.tags.capability.append(c)
    for r in risk:
        if r not in manifest.tags.risk:
            manifest.tags.risk.append(r)  # type: ignore[arg-type]
    for q in quality:
        if q not in manifest.tags.quality:
            manifest.tags.quality.append(q)  # type: ignore[arg-type]
    manifest.touch()
    path = _publisher.save(settings.mcp_state_dir, manifest)
    console.print(f"Updated tags written to {path}")
    console.print_json(data=manifest.model_dump(mode="json"))


@app.command("verify")
def verify_cmd(manifest_id: str = typer.Argument(...)) -> None:
    """Run sandbox install + health check via SelfRepair."""

    settings = get_settings()
    manifest = _publisher.load(settings.mcp_state_dir, manifest_id)
    client = get_client(settings)
    manifest, validation = _verify.verify(manifest, client)
    _publisher.save(settings.mcp_state_dir, manifest)
    console.print_json(
        data={
            "validation": validation.model_dump(mode="json"),
            "status": manifest.status.model_dump(mode="json"),
        }
    )


@app.command("repair")
def repair_cmd(
    manifest_id: str = typer.Argument(...),
    use_gitpilot: bool = typer.Option(False, "--use-gitpilot"),
) -> None:
    """Repair an MCP server (SelfRepair safe -> GitPilot escalation)."""

    settings = get_settings()
    manifest = _publisher.load(settings.mcp_state_dir, manifest_id)
    client = get_client(settings)
    manifest, result, audit = _repair.repair(manifest, client, use_gitpilot=use_gitpilot)
    _publisher.save(settings.mcp_state_dir, manifest)
    console.print_json(
        data={"result": result.model_dump(mode="json"), "audit": audit}
    )


@app.command("report")
def report_cmd(manifest_id: str = typer.Argument(...)) -> None:
    """Pretty-print the current manifest record."""

    settings = get_settings()
    manifest = _publisher.load(settings.mcp_state_dir, manifest_id)
    table = Table(title=f"MCP {manifest_id}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("title", manifest.title or "")
    table.add_row("health", manifest.status.health)
    table.add_row("license", str(manifest.source.license_id))
    table.add_row("latest_verified_commit", manifest.status.latest_verified_commit or "")
    table.add_row("runtimes", ", ".join(manifest.tags.runtime))
    table.add_row("quality", ", ".join(manifest.tags.quality))
    table.add_row("risk", ", ".join(manifest.tags.risk))
    console.print(table)
    console.print_json(data=manifest.model_dump(mode="json"))


@app.command("publish")
def publish_cmd(manifest_id: str = typer.Argument(...)) -> None:
    """Mark the manifest as agent-matrix-verified and persist."""

    settings = get_settings()
    manifest = _publisher.load(settings.mcp_state_dir, manifest_id)
    path = _publisher.publish(settings.mcp_state_dir, manifest)
    console.print(f"Published manifest at {path}")
    console.print_json(data=manifest.model_dump(mode="json"))


@app.command("license-check")
def license_check(
    spdx_id: str = typer.Argument(...),
    allow_strong_copyleft: bool = typer.Option(False, "--allow-strong-copyleft"),
) -> None:
    """Classify an SPDX id against the default policy allowlist."""

    if allow_strong_copyleft:
        from matrix_codex.mcp.license import PolicyClass
        allowed: tuple[PolicyClass, ...] = ("permissive", "weak-copyleft", "strong-copyleft")
        decision = license_decide(spdx_id, allowed_classes=allowed)
    else:
        decision = license_decide(spdx_id)
    console.print(json.dumps(decision.__dict__, indent=2))
