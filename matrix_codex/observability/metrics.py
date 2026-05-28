"""Process-wide Prometheus counters + readiness probe.

Counters initialise lazily so test harness imports don't pay the cost.
Reuse the same metric objects across modules -- they are singletons by
definition in prometheus_client.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from matrix_codex.settings import Settings, get_settings

logger = logging.getLogger(__name__)

_initialised = False
RUNS_TOTAL: Any = None
TASKS_TOTAL: Any = None
DISPATCH_FAILURES_TOTAL: Any = None
SELFREPAIR_CALLS_TOTAL: Any = None
OLLABRIDGE_CALLS_TOTAL: Any = None


def _ensure() -> None:
    global _initialised, RUNS_TOTAL, TASKS_TOTAL, DISPATCH_FAILURES_TOTAL
    global SELFREPAIR_CALLS_TOTAL, OLLABRIDGE_CALLS_TOTAL
    if _initialised:
        return
    try:
        from prometheus_client import Counter
    except ImportError:  # pragma: no cover
        logger.warning("prometheus_client not installed; metrics are no-ops")

        class _Noop:
            def labels(self, **_: Any) -> "_Noop":
                return self

            def inc(self, _v: float = 1.0) -> None:
                return None

        RUNS_TOTAL = TASKS_TOTAL = DISPATCH_FAILURES_TOTAL = _Noop()
        SELFREPAIR_CALLS_TOTAL = OLLABRIDGE_CALLS_TOTAL = _Noop()
        _initialised = True
        return

    RUNS_TOTAL = Counter(
        "matrix_maintainer_runs_total",
        "Controller runs by terminal status.",
        labelnames=("status",),
    )
    TASKS_TOTAL = Counter(
        "matrix_maintainer_tasks_total",
        "Maintenance tasks created by risk level.",
        labelnames=("risk_level",),
    )
    DISPATCH_FAILURES_TOTAL = Counter(
        "matrix_maintainer_dispatch_failures_total",
        "Worker dispatch failures.",
    )
    SELFREPAIR_CALLS_TOTAL = Counter(
        "matrix_maintainer_selfrepair_calls_total",
        "SelfRepair client calls.",
        labelnames=("method", "outcome"),
    )
    OLLABRIDGE_CALLS_TOTAL = Counter(
        "matrix_maintainer_ollabridge_calls_total",
        "OllaBridge chat-completions calls.",
        labelnames=("outcome",),
    )
    _initialised = True


def _module_attribute(name: str) -> Any:
    _ensure()
    return globals()[name]


def __getattr__(name: str) -> Any:  # PEP 562 lazy module attrs
    if name in {
        "RUNS_TOTAL",
        "TASKS_TOTAL",
        "DISPATCH_FAILURES_TOTAL",
        "SELFREPAIR_CALLS_TOTAL",
        "OLLABRIDGE_CALLS_TOTAL",
    }:
        return _module_attribute(name)
    raise AttributeError(name)


def readiness_probe(settings: Settings | None = None) -> dict[str, Any]:
    """Return a structured readiness assessment. Truthy `ready` ==> ok."""

    s = settings or get_settings()
    checks: dict[str, dict[str, Any]] = {}
    ok = True

    def _check_dir(name: str, p: Path) -> None:
        nonlocal ok
        try:
            p.mkdir(parents=True, exist_ok=True)
            probe = p / ".ready_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            checks[name] = {"ok": True, "path": str(p)}
        except Exception as exc:  # noqa: BLE001
            ok = False
            checks[name] = {"ok": False, "path": str(p), "error": str(exc)}

    _check_dir("state_dir", s.state_dir)
    _check_dir("work_dir", s.work_dir)
    _check_dir("mcp_state_dir", s.mcp_state_dir)
    _check_dir("patches_state_dir", s.patches_state_dir)

    checks["ollabridge_configured"] = {
        "ok": True,
        "value": bool(s.ollabridge_api_key),
        "note": "OllaBridge optional at startup; required for LLM calls",
    }
    checks["selfrepair_mode"] = {"ok": True, "value": s.selfrepair_mode}
    checks["github_token_present"] = {"ok": True, "value": bool(s.github_token or s.cross_repo_token)}

    return {"ready": ok, "checks": checks}
