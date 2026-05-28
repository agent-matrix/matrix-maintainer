"""Liveness + readiness FastAPI routes.

Mount via::

    from matrix_codex.api.health import router
    app.include_router(router)

Keep `/health` cheap (no I/O) and `/ready` honest (storage write probe,
config sanity).
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from matrix_codex.observability.metrics import readiness_probe
from matrix_codex.settings import get_settings

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: process is alive. No I/O."""

    return {"status": "ok"}


@router.get("/ready")
def ready(response: Response) -> dict[str, object]:
    """Readiness: storage writable, settings loaded."""

    status = readiness_probe(get_settings())
    if not status["ready"]:
        response.status_code = 503
    return status


@router.get("/metrics")
def metrics() -> Response:
    """Prometheus scrape endpoint."""

    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    except ImportError:
        return Response(content="# prometheus_client not installed\n", media_type="text/plain")
    # Force metric registration to occur before generate_latest.
    from matrix_codex.observability import metrics as _m  # noqa: F401

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
