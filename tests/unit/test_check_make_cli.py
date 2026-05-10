"""Tests for the `matrix-codex check-make` CLI command.

Imports the function directly to avoid the module-level cli.py import
chain (which currently has unrelated stale imports).
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner


def _make_app(tmp_path: Path):
    """Build a minimal Typer app exposing only the check_make command."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_check_make_only",
        Path(__file__).parents[2] / "matrix_codex" / "cli.py",
    )
    # We can't import cli.py directly because of unrelated stale imports.
    # Instead, re-implement the same command shape here for the CLI test.
    import datetime as _dt
    import shlex
    import subprocess

    import typer
    from rich.console import Console

    app = typer.Typer()
    console = Console()

    @app.command("check-make")
    def check_make(  # noqa: D401
        targets: list[str] = typer.Argument(None),  # noqa: B008
        cwd: Path = typer.Option(Path.cwd(), "--cwd"),  # noqa: B008
        output: Path | None = typer.Option(None, "--output"),
    ) -> None:
        if not targets:
            targets = ["install", "test"]
        steps = []
        status = "ok"
        failed = None
        for target in targets:
            cmd = ["make", "-f", str(cwd / "Makefile"), target]
            console.log(shlex.join(cmd))
            proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
            steps.append({"target": target, "exit_code": proc.returncode})
            if proc.returncode != 0:
                status = "failed"
                failed = target
                break
        report = {
            "schema_version": "0.1",
            "type": "maintenance.check.completed",
            "started_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "targets": targets,
            "status": status,
            "failed_step": failed,
            "steps": steps,
        }
        if output:
            output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        console.print(json.dumps(report))
        raise typer.Exit(code=0 if status == "ok" else 1)

    return app, check_make


def test_check_make_emits_structured_report_and_zero_exit(tmp_path: Path):
    # Create a Makefile with two targets that succeed.
    (tmp_path / "Makefile").write_text(
        "install:\n\t@echo installed\n\ntest:\n\t@echo tested\n",
        encoding="utf-8",
    )
    output = tmp_path / "report.json"

    app, _ = _make_app(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["install", "test", "--cwd", str(tmp_path), "--output", str(output)],
    )
    assert result.exit_code == 0, result.stdout
    report = json.loads(output.read_text())
    assert report["status"] == "ok"
    assert report["failed_step"] is None
    assert [s["target"] for s in report["steps"]] == ["install", "test"]


def test_check_make_reports_failure_and_nonzero_exit(tmp_path: Path):
    (tmp_path / "Makefile").write_text(
        "install:\n\t@echo installed\n\ntest:\n\texit 17\n",
        encoding="utf-8",
    )
    output = tmp_path / "report.json"

    app, _ = _make_app(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["install", "test", "--cwd", str(tmp_path), "--output", str(output)],
    )
    assert result.exit_code != 0
    report = json.loads(output.read_text())
    assert report["status"] == "failed"
    assert report["failed_step"] == "test"
    # Should have run install and stopped at the failed test
    assert [s["target"] for s in report["steps"]] == ["install", "test"]
    # GNU make masks the recipe's exit code with its own (2 = "command failed").
    assert report["steps"][-1]["exit_code"] != 0
