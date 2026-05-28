from __future__ import annotations

from matrix_codex.orchestration.pr_body import render
from matrix_codex.selfrepair.dto import (
    HealthIssueDTO,
    JsonReportDTO,
    RepairResultDTO,
    RepoHealthReportDTO,
    RepoRefDTO,
    ValidationReportDTO,
)


def test_render_includes_required_sections() -> None:
    ref = RepoRefDTO(
        full_name="agent-matrix/matrix-hub",
        clone_url="https://github.com/agent-matrix/matrix-hub.git",
    )
    health = RepoHealthReportDTO(
        repo=ref,
        status="degraded",
        issues=[HealthIssueDTO(repo=ref.full_name, issue_type="tests_failing", details="x")],
    )
    repair = RepairResultDTO(
        repo=ref.full_name,
        applied=["makefile"],
        skipped=["tests_failing"],
        failed=[],
        changed_files=["Makefile"],
    )
    validation = ValidationReportDTO(
        repo=ref.full_name,
        install_ok=True,
        test_ok=False,
        sandbox="matrixlab",
    )
    report = JsonReportDTO(
        repo=ref.full_name, health=health, repair=repair, validation=validation
    )
    body = render(report=report, risk_level="medium", operation="repair")

    assert "Matrix-Maintainer" in body
    assert "`medium`" in body
    assert "agent-matrix/matrix-hub" in body
    assert "### Health" in body
    assert "### Repair actions" in body
    assert "### Validation" in body
    assert "makefile" in body
    assert "tests_failing" in body


def test_render_marks_high_risk_as_human_required() -> None:
    ref = RepoRefDTO(full_name="a/b", clone_url="https://github.com/a/b.git")
    health = RepoHealthReportDTO(repo=ref, status="down")
    report = JsonReportDTO(repo="a/b", health=health)
    body = render(report=report, risk_level="high", operation="repair")
    assert "Explicit human approval required" in body


def test_render_gitpilot_label_flag() -> None:
    ref = RepoRefDTO(full_name="a/b", clone_url="https://github.com/a/b.git")
    health = RepoHealthReportDTO(repo=ref, status="healthy")
    report = JsonReportDTO(repo="a/b", health=health)
    body = render(report=report, risk_level="low", operation="repair", use_gitpilot=True)
    assert "GitPilot" in body
