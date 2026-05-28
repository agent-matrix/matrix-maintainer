from __future__ import annotations

import pytest

from matrix_codex.llm import (
    OllaBridgeClient,
    OllaBridgeUnavailable,
    openai_compatible_env,
)
from matrix_codex.settings import Settings


def test_client_unconfigured_raises() -> None:
    client = OllaBridgeClient(
        base_url="https://api.ollabridge.com/v1",
        api_key=None,
        default_model="qwen2.5:7b",
    )
    assert client.configured is False
    with pytest.raises(OllaBridgeUnavailable):
        client.chat([{"role": "user", "content": "hi"}])


def test_openai_compatible_env_keys() -> None:
    settings = Settings(
        OLLABRIDGE_BASE_URL="https://api.ollabridge.com/v1",
        OLLABRIDGE_API_KEY="ob_test",
        OLLABRIDGE_MODEL="qwen2.5:7b",
    )
    env = openai_compatible_env(settings)
    assert env["OPENAI_BASE_URL"] == "https://api.ollabridge.com/v1"
    assert env["OPENAI_API_BASE"] == "https://api.ollabridge.com/v1"
    assert env["OPENAI_API_KEY"] == "ob_test"
    assert env["OLLABRIDGE_API_KEY"] == "ob_test"
    assert env["OLLABRIDGE_MODEL"] == "qwen2.5:7b"


def test_openai_compatible_env_omits_unset_key() -> None:
    settings = Settings(
        OLLABRIDGE_BASE_URL="https://api.ollabridge.com/v1",
        OLLABRIDGE_API_KEY=None,
    )
    env = openai_compatible_env(settings)
    assert "OPENAI_API_KEY" not in env
    assert env["OPENAI_BASE_URL"] == "https://api.ollabridge.com/v1"


def test_client_chat_calls_chat_completions(respx_mock) -> None:
    import httpx

    route = respx_mock.post("https://api.ollabridge.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "x",
                "model": "qwen2.5:7b",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
            },
        )
    )
    client = OllaBridgeClient(
        base_url="https://api.ollabridge.com/v1",
        api_key="ob_test",
        default_model="qwen2.5:7b",
    )
    resp = client.chat([{"role": "user", "content": "hi"}])
    assert resp.content == "ok"
    assert resp.model == "qwen2.5:7b"
    assert route.called
    sent = route.calls.last.request
    assert sent.headers["Authorization"] == "Bearer ob_test"
