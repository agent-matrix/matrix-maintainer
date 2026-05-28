"""Public protocol for the SelfRepair boundary.

Everything Matrix-Maintainer needs from SelfRepair flows through this
Protocol. Implementations: :class:`SelfRepairLocalClient`,
:class:`SelfRepairHttpClient`.

The contract is intentionally small. If you find yourself adding a
seventh method, push the work inside an existing call's metadata or
introduce a new DTO, but do not let the surface area drift.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from matrix_codex.selfrepair.dto import (
    HealthIssueDTO,
    JsonReportDTO,
    RepairResultDTO,
    RepoHealthReportDTO,
    RepoRefDTO,
    ValidationReportDTO,
)


class SelfRepairError(RuntimeError):
    """Raised when the SelfRepair backend fails.

    The orchestrator catches this, records the failure, and continues
    with the next repo -- a SelfRepair failure is never allowed to
    crash the control plane.
    """


@runtime_checkable
class SelfRepairClient(Protocol):
    """Stable client contract for the SelfRepair engine."""

    def scan(self, repo: RepoRefDTO, *, profile: str | None = None) -> RepoHealthReportDTO:
        """Scan a repository and return a structured health report."""

    def repair(
        self,
        repo: RepoRefDTO,
        issues: list[HealthIssueDTO],
        *,
        safe_only: bool = True,
        branch: str | None = None,
    ) -> RepairResultDTO:
        """Attempt safe deterministic repairs for the given issues."""

    def validate(
        self,
        repo: RepoRefDTO,
        *,
        in_sandbox: bool = True,
    ) -> ValidationReportDTO:
        """Validate install / test / start, ideally in a sandbox."""

    def report(self, repo: RepoRefDTO) -> JsonReportDTO:
        """Return the most recent aggregate report for the repo."""
