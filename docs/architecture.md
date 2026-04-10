# Architecture

`matrix-codex` is the central orchestration repository for multi-repository maintenance.

## Layers

1. **Controller** (`matrix_codex.cli`, `matrix_codex.main`) discovers repositories, chooses execution mode, and writes state snapshots.
2. **Planner** (`matrix_codex/codex`) builds operation prompts and applies risk policy defaults.
3. **Executor** (`matrix_codex/orchestration`) dispatches `matrix-codex-worker.yml` into target repositories.
4. **Reporter** (`matrix_codex/reporting`, `matrix_codex/site`) publishes JSON status artifacts and the static dashboard.

## Execution model

- **Dispatch mode (default)**: `run-daily` triggers target repository worker workflows.
- **Local mode**: retains legacy clone/analyze/heal flow for a single-repo fallback.

## Controller and worker split

The controller does not edit all repositories in one checkout. Instead, each managed repository executes maintenance in its own workflow context and reports status back through artifacts/state.
