from pathlib import Path

from matrix_codex.health_scanner import HealthScanner, ScannerConfig


def test_health_scanner_returns_issues(tmp_path: Path) -> None:
    repos = tmp_path / "repositories.yml"
    repos.write_text(
        "repositories:\n"
        "  - name: agent-matrix/repo-a\n"
        "    profile: python-service\n"
        "    run_tests: true\n",
        encoding="utf-8",
    )

    scanner = HealthScanner(ScannerConfig(repositories_file=repos))
    issues = scanner.scan()

    assert len(issues) >= 1
    assert issues[0].repo == "agent-matrix/repo-a"
