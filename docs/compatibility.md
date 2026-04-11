# Compatibility Matrix

This document clarifies current compatibility status for model/runtime backends.

## Current status

| Integration | Current status | Evidence in repo | Next step |
|---|---|---|---|
| Ollama | Partial | `app/agents/ollama_agent.py` exists but returns `not_implemented`. | Implement real Ollama HTTP client flow and task execution contract. |
| OllamaBridge | Planned | No dedicated bridge adapter/module found in repository. | Add `matrix_codex/integration/ollamabridge_client.py` and wire into agent factory. |
| Hugging Face Spaces | Supported | `.github/workflows/sync-matrix-codex-status-to-hf-space.yml` deploys apps + Dockerfile to Space. | Keep secrets configured and monitor deploy retries/logs. |

## Verification checklist

1. **Ollama**
   - Add endpoint configuration (`OLLAMA_BASE_URL`, model ID).
   - Implement real inference call and structured response parsing.
   - Add integration test for model request/response + fallback behavior.

2. **OllamaBridge**
   - Define bridge API contract (task payload, response schema, error schema).
   - Add adapter class and feature flag in settings.
   - Add health check command in CLI.

3. **Hugging Face**
   - Confirm secrets: `HF_TOKEN`, `HF_USERNAME`, `SPACE_NAME`.
   - Validate workflow triggers on app/deploy changes.
   - Verify published Space URL returns healthy backend/frontend.

## Recommendation

Treat Ollama/OllamaBridge as **incremental enhancements** while continuing to run the proven GitHub Actions worker path for production maintenance dispatch.
