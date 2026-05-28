from __future__ import annotations

import pytest

from matrix_codex.selfrepair import (
    HealthIssueDTO,
    RepoHealthReportDTO,
    RepoRefDTO,
    SCHEMA_VERSION,
    SelfRepairClient,
    SelfRepairLocalClient,
    get_client,
)


@pytest.fixture()
def repo() -> RepoRefDTO:
    return RepoRefDTO(
        full_name="agent-matrix/matrix-hub",
        clone_url="https://github.com/agent-matrix/matrix-hub.git",
        default_branch="main",
    )


def test_local_client_implements_protocol() -> None:
    client = SelfRepairLocalClient()
    assert isinstance(client, SelfRepairClient)


def test_local_client_scan_returns_health_dto(tmp_path, repo: RepoRefDTO) -> None:
    repos_file = tmp_path / "repositories.yml"
    repos_file.write_text(
        "repositories:\n"
        f"  - name: {repo.full_name}\n"
        "    run_tests: true\n"
        "    dependency_maintenance: false\n",
        encoding="utf-8",
    )
    client = SelfRepairLocalClient(repositories_file=repos_file)
    report = client.scan(repo)

    assert isinstance(report, RepoHealthReportDTO)
    assert report.schema_version == SCHEMA_VERSION
    assert report.repo.full_name == repo.full_name
    # one issue expected (ci_missing_recent_success) since run_tests=true.
    assert any(i.issue_type == "ci_missing_recent_success" for i in report.issues)


def test_local_client_repair_escalates_when_not_safe_only(repo: RepoRefDTO) -> None:
    client = SelfRepairLocalClient()
    issues = [HealthIssueDTO(repo=repo.full_name, issue_type="tests_failing", details="x")]
    result = client.repair(repo, issues, safe_only=False)
    assert result.needs_escalation is True
    assert "tests_failing" in result.skipped


def test_factory_returns_local_when_no_base_url(monkeypatch) -> None:
    from matrix_codex.settings import Settings

    settings = Settings(SELFREPAIR_MODE="auto", SELFREPAIR_BASE_URL=None)
    client = get_client(settings)
    assert isinstance(client, SelfRepairLocalClient)


def test_factory_returns_http_when_base_url_set() -> None:
    from matrix_codex.selfrepair.http_client import SelfRepairHttpClient
    from matrix_codex.settings import Settings

    settings = Settings(SELFREPAIR_MODE="auto", SELFREPAIR_BASE_URL="https://selfrepair.example")
    client = get_client(settings)
    assert isinstance(client, SelfRepairHttpClient)


def test_factory_rejects_http_without_base_url() -> None:
    from matrix_codex.settings import Settings

    settings = Settings(SELFREPAIR_MODE="http", SELFREPAIR_BASE_URL=None)
    with pytest.raises(ValueError):
        get_client(settings)
