"""OllaBridge Cloud client -- the only LLM gateway in matrix-maintainer.

OllaBridge exposes an OpenAI-compatible API at
``${OLLABRIDGE_BASE_URL}/chat/completions`` (default base:
``https://api.ollabridge.com/v1``). Auth is
``Authorization: Bearer ob_...`` (admin-issued bearer token, prefix
``ob_``). The OpenAI-compatible shape means existing OpenAI-SDK code
works by overriding `OPENAI_BASE_URL` and `OPENAI_API_KEY` -- see
:func:`openai_compatible_env` and the GitPilot client.

This module deliberately does NOT depend on the openai SDK -- one less
transitive dep, and the surface we use is small enough that an httpx
client is clearer.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal, TypedDict

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from matrix_codex.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class ChatMessage(TypedDict, total=False):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str
    tool_call_id: str


class OllaBridgeError(RuntimeError):
    """Raised for non-recoverable failures from the gateway."""


class OllaBridgeUnavailable(OllaBridgeError):
    """Raised when the gateway is not configured (no API key).

    Callers should treat this as a soft signal -- fall back to a
    deterministic local path (e.g. a stub planner) rather than crashing.
    """


@dataclass(slots=True)
class ChatResponse:
    content: str
    model: str
    usage: dict[str, Any]
    raw: dict[str, Any]


class OllaBridgeClient:
    """Minimal OpenAI-compatible chat-completions client for OllaBridge."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        default_model: str,
        timeout_seconds: float = 120.0,
        organization: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model
        self._timeout = timeout_seconds
        self._organization = organization
        self._client = http_client or httpx.Client(timeout=httpx.Timeout(timeout_seconds))

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def default_model(self) -> str:
        return self._default_model

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> ChatResponse:
        if not self.configured:
            raise OllaBridgeUnavailable("OLLABRIDGE_API_KEY is not set")
        body: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": list(messages),
        }
        if temperature is not None:
            body["temperature"] = temperature
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if extra:
            body.update(extra)

        payload = self._post("/chat/completions", body)
        try:
            choice = payload["choices"][0]
            content = choice["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise OllaBridgeError(f"malformed_chat_completion: {payload!r}") from exc
        return ChatResponse(
            content=content,
            model=payload.get("model", body["model"]),
            usage=payload.get("usage", {}) or {},
            raw=payload,
        )

    @retry(
        reraise=True,
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
    )
    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": "matrix-maintainer/0.2 (+https://github.com/agent-matrix/matrix-maintainer)",
        }
        if self._organization:
            headers["OpenAI-Organization"] = self._organization
        url = f"{self._base_url}{path}"
        resp = self._client.post(url, headers=headers, json=body)
        if resp.status_code >= 500:
            resp.raise_for_status()
        if resp.status_code >= 400:
            raise OllaBridgeError(f"ollabridge_http_{resp.status_code}: {resp.text[:500]}")
        return resp.json()

    def close(self) -> None:  # pragma: no cover - lifecycle
        self._client.close()


@lru_cache(maxsize=1)
def get_llm_client(settings: Settings | None = None) -> OllaBridgeClient:
    """Return a singleton OllaBridge client built from settings."""

    s = settings or get_settings()
    return OllaBridgeClient(
        base_url=s.ollabridge_base_url,
        api_key=s.ollabridge_api_key,
        default_model=s.ollabridge_model,
        timeout_seconds=s.ollabridge_timeout_seconds,
        organization=s.ollabridge_organization,
    )


def openai_compatible_env(settings: Settings | None = None) -> dict[str, str]:
    """Env vars that point OpenAI-SDK clients at OllaBridge.

    Use this when spawning external processes (e.g. GitPilot) that
    already speak OpenAI -- inject the returned dict into ``subprocess.run
    (env=...)``. Keys are only included when they have a value.
    """

    s = settings or get_settings()
    env: dict[str, str] = {
        "OPENAI_BASE_URL": s.ollabridge_base_url,
        # OpenAI Python SDK historically used OPENAI_API_BASE -- include both for
        # broad compatibility with older clients.
        "OPENAI_API_BASE": s.ollabridge_base_url,
    }
    if s.ollabridge_api_key:
        env["OPENAI_API_KEY"] = s.ollabridge_api_key
    if s.ollabridge_organization:
        env["OPENAI_ORG_ID"] = s.ollabridge_organization
    if s.ollabridge_model:
        env["OLLABRIDGE_MODEL"] = s.ollabridge_model
    # Also export the raw OllaBridge env so downstream tools can pick the
    # right variable name on their own.
    env["OLLABRIDGE_BASE_URL"] = s.ollabridge_base_url
    if s.ollabridge_api_key:
        env["OLLABRIDGE_API_KEY"] = s.ollabridge_api_key
    return env


def merged_subprocess_env(settings: Settings | None = None) -> dict[str, str]:
    """OS env + openai_compatible_env, ready to pass to subprocess.run."""

    env = os.environ.copy()
    env.update(openai_compatible_env(settings))
    return env
