"""SelfRepair client adapter.

This package is the single boundary between Matrix-Maintainer and
SelfRepair. Everything Matrix-Maintainer needs from SelfRepair --
scanning, repair, sandbox validation, reporting -- goes through the
`SelfRepairClient` Protocol defined in :mod:`matrix_codex.selfrepair.client`.

Two implementations ship out of the box:

* :class:`SelfRepairLocalClient` -- runs in-process; uses the SelfRepair
  library if importable, otherwise falls back to Matrix Codex internal
  modules during the migration window.
* :class:`SelfRepairHttpClient` -- calls SelfRepair's stable
  ``/v1/rpc`` JSON-RPC surface over HTTP.

Use :func:`get_client` to pick the right one based on settings.
"""

from matrix_codex.selfrepair.client import SelfRepairClient, SelfRepairError
from matrix_codex.selfrepair.dto import (
    HealthIssueDTO,
    JsonReportDTO,
    RepairResultDTO,
    RepoRefDTO,
    RepoHealthReportDTO,
    ValidationReportDTO,
    SCHEMA_VERSION,
)
from matrix_codex.selfrepair.factory import get_client
from matrix_codex.selfrepair.local_client import SelfRepairLocalClient
from matrix_codex.selfrepair.http_client import SelfRepairHttpClient

__all__ = [
    "SCHEMA_VERSION",
    "HealthIssueDTO",
    "JsonReportDTO",
    "RepairResultDTO",
    "RepoHealthReportDTO",
    "RepoRefDTO",
    "SelfRepairClient",
    "SelfRepairError",
    "SelfRepairHttpClient",
    "SelfRepairLocalClient",
    "ValidationReportDTO",
    "get_client",
]
