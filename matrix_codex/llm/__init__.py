"""LLM gateway for matrix-maintainer.

This package is the single point through which matrix-maintainer talks
to language models. Currently it speaks the OpenAI-compatible API of
OllaBridge Cloud (enterprise). The OpenAI-compatible surface means any
third-party tool that already speaks OpenAI -- including GitPilot --
automatically works by overriding `OPENAI_BASE_URL` and `OPENAI_API_KEY`.

If you need a new LLM call from inside matrix-maintainer, import the
client from here:

    from matrix_codex.llm import get_llm_client, OllaBridgeClient

    client = get_llm_client()
    msg = client.chat([{"role": "user", "content": "..."}])

Never import the OpenAI SDK or any other LLM SDK directly elsewhere in
this codebase -- the gateway is the boundary.
"""

from matrix_codex.llm.ollabridge import (
    ChatMessage,
    OllaBridgeClient,
    OllaBridgeError,
    OllaBridgeUnavailable,
    get_llm_client,
    openai_compatible_env,
)

__all__ = [
    "ChatMessage",
    "OllaBridgeClient",
    "OllaBridgeError",
    "OllaBridgeUnavailable",
    "get_llm_client",
    "openai_compatible_env",
]
