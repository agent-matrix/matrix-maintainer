# AI Maintainer Guide

This guide is the operational handoff for AI agents (Codex/GitPilot/Ollama) and humans maintaining `matrix-codex`.

## Purpose

`matrix-codex` is a controller that scans repository health, plans maintenance tasks, applies governance + budget checks, dispatches worker workflows, and tracks outcomes.

## End-to-end loop

1. **Scan**: `matrix-codex scan-health`
2. **Plan**: `matrix-codex plan-maintenance`
3. **Execute**: `matrix-codex run-maintenance`
4. **Report**: `matrix-codex report-status`

The daily orchestrator uses the same flow in `.github/workflows/matrix-maintainer-orchestrator.yml`.

## Key files for AI agents

- `matrix_codex/health_scanner.py`: issue detection
- `matrix_codex/task_engine.py`: issue -> task mapping
- `matrix_codex/main.py`: orchestration flow
- `matrix_codex/orchestration/dispatcher.py`: GitHub dispatch contract (`run_id`, `task_json`)
- `matrix_codex/storage/models.py`: persistent records
- `config/repositories.yml`: per-repo profiles and tasks
- `config/policies.yml`: policy guardrails
- `config/tasks.yml`: task routing and path allowances

## Rules for safe modifications

1. Never push directly to `main`; always use PRs.
2. Keep changes scoped to allowed paths from task/policy configs.
3. Do not mutate secrets, workflow permissions, or auth configuration without explicit approval.
4. If tests fail before the change, document baseline failures in PR notes.

## Adding a new health issue type

1. Add issue production logic in `health_scanner.py`.
2. Add mapping in `task_engine.py` (`ISSUE_TO_TASK`).
3. Add task config defaults/overrides in `config/tasks.yml`.
4. Add unit tests in `tests/unit/test_health_scanner.py` and `tests/unit/test_task_engine.py`.

## Adding a new repository profile

1. Add profile install/test/lint commands to `config/repositories.yml`.
2. Add repository task/risk metadata under `repositories:`.
3. Validate by running:

```bash
PYTHONPATH=. pytest -q
PYTHONPATH=. matrix-codex scan-health
PYTHONPATH=. matrix-codex plan-maintenance
```

## Event model and troubleshooting

- Events are persisted in `state/maintainer_records.json` via `StorageDB`.
- Backend serves status at `/status` and maintainer records under `/maintainer/*`.

If dispatch fails:

- Verify `GITHUB_TOKEN` or `CROSS_REPO_TOKEN` exists.
- Verify target repo has `matrix-maintainer.yml` workflow installed.
- Verify `WORKER_WORKFLOW_FILE` in settings matches workflow filename.

## Developer commands

```bash
make install
make test
PYTHONPATH=. pytest -q tests/unit/test_health_scanner.py tests/unit/test_task_engine.py tests/unit/test_gitpilot_runner.py
```

If network restrictions prevent dependency download, run with the existing local environment and report the limitation.
