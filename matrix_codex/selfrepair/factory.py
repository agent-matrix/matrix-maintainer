"""Pick the right SelfRepair client based on settings."""

from __future__ import annotations

import logging

from matrix_codex.selfrepair.client import SelfRepairClient
from matrix_codex.selfrepair.http_client import SelfRepairHttpClient
from matrix_codex.selfrepair.local_client import SelfRepairLocalClient
from matrix_codex.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def get_client(settings: Settings | None = None) -> SelfRepairClient:
    """Return a SelfRepair client honoring ``SELFREPAIR_MODE``.

    * ``http``  -> :class:`SelfRepairHttpClient` (requires ``SELFREPAIR_BASE_URL``)
    * ``local`` -> :class:`SelfRepairLocalClient`
    * ``auto``  -> http if a base URL is set, otherwise local.
    """

    s = settings or get_settings()
    mode = (s.selfrepair_mode or "auto").lower()
    base_url = s.selfrepair_base_url

    if mode == "http" or (mode == "auto" and base_url):
        if not base_url:
            raise ValueError("SELFREPAIR_MODE=http but SELFREPAIR_BASE_URL is not set")
        logger.info("selfrepair_client=http", extra={"base_url": base_url})
        return SelfRepairHttpClient(
            base_url=base_url,
            api_key=s.selfrepair_api_key,
            timeout_seconds=s.selfrepair_timeout_seconds,
        )

    logger.info("selfrepair_client=local")
    return SelfRepairLocalClient()
