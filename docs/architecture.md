# Architecture

`matrix-codex` is the central orchestration repository for multi-repository maintenance.

## Core components

1. **Health Scanner** (`matrix_codex/health_scanner.py`) discovers maintenance issues across repositories.
2. **Task Engine** (`matrix_codex/task_engine.py`) maps health issues into executable maintenance tasks.
3. **Agent-Matrix Integration** (`matrix_codex/agent_matrix/init.py`) coordinates Matrix AI planning, Guardian approvals, Treasury checks, and Hub event publication.
4. **GitPilot Runner** (`matrix_codex/gitpilot/runner.py`) executes multi-agent repair loops and returns structured execution results.
5. **Dispatcher** (`matrix_codex/orchestration/dispatcher.py`) dispatches `matrix-maintainer.yml` workflows in target repositories.
6. **Persistent Storage** (`matrix_codex/storage/models.py`) stores runs, tasks, events, health scans, and PR records for auditability.
7. **Status API + Dashboard** (`apps/backend/main.py`, `matrix_codex/api/routes.py`, `matrix_codex/site/generator.py`) exposes maintenance state to operators.

## Maintenance loop

```text
scan -> plan -> approve -> budget-check -> execute -> reconcile -> learn
```

- **Scan**: detect failing CI, stale dependencies, lint and test issues.
- **Plan**: convert issues to tasks and request Matrix AI decomposition.
- **Approve**: enforce policy limits through Guardian-compatible checks.
- **Budget-check**: verify available MXU budget before execution.
- **Execute**: dispatch worker workflows that run GitPilot agents.
- **Reconcile**: persist events/results and update status APIs/site.
- **Learn**: store outcomes in Matrix Hub for future reuse.

## Controller and worker split

The controller does not edit all repositories in one checkout. Instead, each managed repository executes maintenance in its own workflow context and reports status back to this control plane.
