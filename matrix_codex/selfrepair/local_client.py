"""In-process SelfRepair client.

Resolution order:

1. If the ``selfrepair`` library is importable, delegate to it via a
   thin adapter (preferred, production path once SelfRepair publishes
   its in-process API).
2. Otherwise, fall back to existing Matrix Codex internal modules
   (health_scanner, healing/, matrixlab, reporting/). This makes the
   migration safe: the boundary is in place even before the SelfRepair
   library exposes the contract.

The two paths are gated by a feature probe so users see the same
behaviour regardless of which one is active.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

from matrix_codex.selfrepair.client import SelfRepairClient, SelfRepairError
from matrix_codex.selfrepair.dto import (
    HealthIssueDTO,
    JsonReportDTO,
    RepairResultDTO,
    RepoHealthReportDTO,
    RepoRefDTO,
    ValidationReportDTO,
)

logger = logging.getLogger(__name__)


def _try_import_selfrepair() -> Any | None:
    try:
        return importlib.import_module("selfrepair")
    except ImportError:
        return None


class SelfRepairLocalClient(SelfRepairClient):
    """Concrete in-process client."""

    def __init__(self, *, repositories_file: Path | None = None) -> None:
        self._selfrepair = _try_import_selfrepair()
        self._repositories_file = repositories_file or Path("config/repositories.yml")
        self._using_library = self._selfrepair is not None
        logger.info(
            "selfrepair_local_client_init",
            extra={"using_library": self._using_library},
        )

    # ----- public API -----------------------------------------------------

    def scan(self, repo: RepoRefDTO, *, profile: str | None = None) -> RepoHealthReportDTO:
        if self._using_library:
            return self._scan_via_library(repo, profile)
        return self._scan_via_internal(repo, profile)

    def repair(
        self,
        repo: RepoRefDTO,
        issues: list[HealthIssueDTO],
        *,
        safe_only: bool = True,
        branch: str | None = None,
    ) -> RepairResultDTO:
        if self._using_library:
            return self._repair_via_library(repo, issues, safe_only, branch)
        return self._repair_via_internal(repo, issues, safe_only, branch)

    def validate(
        self,
        repo: RepoRefDTO,
        *,
        in_sandbox: bool = True,
    ) -> ValidationReportDTO:
        if self._using_library:
            return self._validate_via_library(repo, in_sandbox)
        return self._validate_via_internal(repo, in_sandbox)

    def report(self, repo: RepoRefDTO) -> JsonReportDTO:
        # No external state store yet; assemble from a fresh scan.
        try:
            health = self.scan(repo)
        except SelfRepairError:
            health = None
        return JsonReportDTO(repo=repo.full_name, health=health)

    # ----- library path (preferred) ---------------------------------------

    def _scan_via_library(self, repo: RepoRefDTO, profile: str | None) -> RepoHealthReportDTO:
        try:
            scanner_mod = importlib.import_module("selfrepair.scanners")
            scan_fn = getattr(scanner_mod, "scan_repo", None)
            if scan_fn is None:
                raise AttributeError("selfrepair.scanners.scan_repo not exported")
            raw = scan_fn(repo.full_name, profile=profile)
            return _normalize_health(raw, repo)
        except Exception as exc:  # pragma: no cover - library shape varies
            logger.warning("selfrepair_library_scan_failed: %s", exc)
            return self._scan_via_internal(repo, profile)

    def _repair_via_library(
        self,
        repo: RepoRefDTO,
        issues: list[HealthIssueDTO],
        safe_only: bool,
        branch: str | None,
    ) -> RepairResultDTO:
        try:
            healing_mod = importlib.import_module("selfrepair.healing")
            heal_fn = getattr(healing_mod, "heal_repo", None)
            if heal_fn is None:
                raise AttributeError("selfrepair.healing.heal_repo not exported")
            raw = heal_fn(
                repo.full_name,
                issues=[i.model_dump(mode="json") for i in issues],
                safe_only=safe_only,
                branch=branch,
            )
            return _normalize_repair(raw, repo.full_name)
        except Exception as exc:  # pragma: no cover
            logger.warning("selfrepair_library_repair_failed: %s", exc)
            return self._repair_via_internal(repo, issues, safe_only, branch)

    def _validate_via_library(self, repo: RepoRefDTO, in_sandbox: bool) -> ValidationReportDTO:
        try:
            mod = importlib.import_module("selfrepair.matrixlab")
            validate_fn = getattr(mod, "validate_repo", None)
            if validate_fn is None:
                raise AttributeError("selfrepair.matrixlab.validate_repo not exported")
            raw = validate_fn(repo.full_name, in_sandbox=in_sandbox)
            return _normalize_validation(raw, repo.full_name)
        except Exception as exc:  # pragma: no cover
            logger.warning("selfrepair_library_validate_failed: %s", exc)
            return self._validate_via_internal(repo, in_sandbox)

    # ----- internal fallback path -----------------------------------------

    def _scan_via_internal(self, repo: RepoRefDTO, profile: str | None) -> RepoHealthReportDTO:
        # Bridge to the existing Matrix Codex scanner so the boundary is
        # live without requiring the SelfRepair library yet.
        from matrix_codex.health_scanner import HealthScanner, ScannerConfig

        scanner = HealthScanner(ScannerConfig(repositories_file=self._repositories_file))
        raw_issues = scanner.scan()
        issues = [
            HealthIssueDTO(
                repo=i.repo,
                issue_type=i.issue_type,
                details=i.details,
                severity=_severity(i.severity),
                metadata={**i.metadata, "profile": profile} if profile else dict(i.metadata),
            )
            for i in raw_issues
            if i.repo == repo.full_name or i.repo.endswith("/" + repo.full_name.split("/")[-1])
        ]
        status = "degraded" if issues else "healthy"
        return RepoHealthReportDTO(repo=repo, status=status, issues=issues, notes=["source=matrix_codex.health_scanner"])

    def _repair_via_internal(
        self,
        repo: RepoRefDTO,
        issues: list[HealthIssueDTO],
        safe_only: bool,
        branch: str | None,
    ) -> RepairResultDTO:
        # No real fixer in matrix_codex/healing yet -- return a structured
        # "needs escalation" so the orchestrator can route to GitPilot.
        return RepairResultDTO(
            repo=repo.full_name,
            applied=[],
            skipped=[i.issue_type for i in issues],
            failed=[],
            branch=branch,
            needs_escalation=not safe_only,
            escalation_reason="local_fallback_no_safe_fixers_registered",
            metadata={"safe_only": safe_only},
        )

    def _validate_via_internal(self, repo: RepoRefDTO, in_sandbox: bool) -> ValidationReportDTO:
        # Without a real sandbox bridge yet, return "unknown" honestly.
        return ValidationReportDTO(
            repo=repo.full_name,
            sandbox="matrixlab" if in_sandbox else "none",
            notes=["local_fallback_no_validator_wired"],
        )


# ---------------------------------------------------------------------------
# normalization helpers
# ---------------------------------------------------------------------------


def _severity(value: Any) -> Any:
    allowed = {"low", "medium", "high", "critical"}
    if isinstance(value, str) and value in allowed:
        return value
    return "medium"


def _normalize_health(raw: Any, repo: RepoRefDTO) -> RepoHealthReportDTO:
    if isinstance(raw, RepoHealthReportDTO):
        return raw
    if hasattr(raw, "model_dump"):
        raw = raw.model_dump()
    if isinstance(raw, dict):
        issues_raw = raw.get("issues", [])
        issues = [
            HealthIssueDTO(
                repo=i.get("repo", repo.full_name),
                issue_type=i.get("issue_type", "unknown"),
                details=i.get("details", ""),
                severity=_severity(i.get("severity", "medium")),
                metadata=i.get("metadata", {}) or {},
            )
            for i in issues_raw
        ]
        return RepoHealthReportDTO(
            repo=repo,
            status=raw.get("status", "unknown"),
            issues=issues,
            notes=list(raw.get("notes", []) or []),
            metadata=raw.get("metadata", {}) or {},
        )
    raise SelfRepairError(f"unrecognized selfrepair health response: {type(raw)!r}")


def _normalize_repair(raw: Any, repo_full: str) -> RepairResultDTO:
    if isinstance(raw, RepairResultDTO):
        return raw
    if hasattr(raw, "model_dump"):
        raw = raw.model_dump()
    if isinstance(raw, dict):
        return RepairResultDTO(
            repo=raw.get("repo", repo_full),
            applied=list(raw.get("applied", []) or []),
            skipped=list(raw.get("skipped", []) or []),
            failed=list(raw.get("failed", []) or []),
            changed_files=list(raw.get("changed_files", []) or []),
            branch=raw.get("branch"),
            needs_escalation=bool(raw.get("needs_escalation", False)),
            escalation_reason=raw.get("escalation_reason"),
            metadata=raw.get("metadata", {}) or {},
        )
    raise SelfRepairError(f"unrecognized selfrepair repair response: {type(raw)!r}")


def _normalize_validation(raw: Any, repo_full: str) -> ValidationReportDTO:
    if isinstance(raw, ValidationReportDTO):
        return raw
    if hasattr(raw, "model_dump"):
        raw = raw.model_dump()
    if isinstance(raw, dict):
        return ValidationReportDTO(
            repo=raw.get("repo", repo_full),
            install_ok=bool(raw.get("install_ok", False)),
            test_ok=bool(raw.get("test_ok", False)),
            start_ok=bool(raw.get("start_ok", False)),
            health_test_ok=bool(raw.get("health_test_ok", False)),
            sandbox=raw.get("sandbox", "none"),
            notes=list(raw.get("notes", []) or []),
            metadata=raw.get("metadata", {}) or {},
        )
    raise SelfRepairError(f"unrecognized selfrepair validation response: {type(raw)!r}")
