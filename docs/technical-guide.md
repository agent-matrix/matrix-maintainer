# Matrix Codex Technical Guide

This guide explains how `matrix-codex` works, how to install it, how to configure credentials, and how to set up Codex-oriented workflows.

## 1. How the Repository Works

`matrix-codex` uses a **controller/worker architecture**:

- **Controller (this repo)**
  - Discovers repositories
  - Selects operation(s)
  - Dispatches workflow runs in target repos
  - Collects and publishes results

- **Worker (target repo workflow)**
  - Runs operation in repository-local context
  - Executes repo-native tests/lint/build
  - Commits and opens PR when changes exist

- **Reporting layer**
  - Writes state snapshots to `state/`
  - Serves status through backend API and frontend dashboard

## 2. Installation

### Prerequisites

- Python `3.11`
- `uv` package manager
- GitHub access token(s)
- Optional: Docker + Docker Compose

### Install project dependencies

```bash
uv sync
```

### Verify CLI

```bash
matrix-codex --help
```

## 3. Configuration

### Repository inventory

Edit:

- `config/repositories.yml`

This file defines:

- organization name
- default branch
- repositories list
- optional repo metadata (`stack`, `profile`, `branch`)
- profile policy defaults

### Environment variables

| Variable | Required | Purpose |
|---|---:|---|
| `GITHUB_TOKEN` | optional | General GitHub auth |
| `CROSS_REPO_TOKEN` | recommended | Dispatch workflows in other repos |
| `GITHUB_ORG` | optional | Default org override |
| `MATRIX_CODEX_EXECUTION_MODE` | optional | `dispatch` (default) or `local` |
| `MATRIX_CODEX_OPERATION` | optional | operation name for runs |

## 4. Credentials and Permissions

For production orchestration, use a PAT or GitHub App token in `CROSS_REPO_TOKEN`.

Recommended permissions:

- **Repository Contents**: read/write (when workers commit)
- **Actions**: read/write (workflow dispatch)
- **Pull Requests**: read/write (create/update PRs)

Store credentials in GitHub Actions secrets for this repository.

## 5. Usage Commands

### Discover repositories

```bash
matrix-codex discover
```

### Run daily orchestration

```bash
matrix-codex run-daily
```

### Check one repository in local mode

```bash
MATRIX_CODEX_EXECUTION_MODE=local matrix-codex check-repo agent-matrix/matrix-hub
```

### Publish static status site

```bash
matrix-codex publish-site
```

## 6. GitHub Workflows

Core workflows in this repo:

- `.github/workflows/orchestrate-agent-matrix.yml`
- `.github/workflows/daily-orchestrator.yml`
- `.github/workflows/manual-orchestrator.yml`
- `.github/workflows/validate-config.yml`

Worker templates:

- `.github/workflows/repo-maintenance-worker.yml` (reusable template)
- `target-repo-template/.github/workflows/matrix-codex-worker.yml` (target repo starter)

## 7. Codex Setup Guidance

`matrix-codex` is designed to work with Codex-style maintenance flows.

Recommended setup:

1. Keep operation definitions explicit (`maintenance`, `lint-fix`, `test-only`, etc.).
2. Add repository-specific policies/instructions in `AGENTS.md` in each managed repo.
3. Use profile metadata in `config/repositories.yml` to control safe defaults.
4. Keep mutation operations PR-based and human-reviewed for high-risk repos.

## 8. Status Dashboard

Dashboard components:

- Backend: `apps/backend/main.py` (FastAPI)
- Frontend: `apps/frontend` (Next.js)

Backend endpoints:

- `GET /health`
- `GET /status`
- `POST /event`
- `WS /ws`

Local run:

```bash
docker compose up --build
```

## 9. Deployment (Docker / Hugging Face)

Root `Dockerfile` builds frontend and runs backend + frontend in one container.

- Frontend exposed on port `7860` (Spaces-compatible)
- Backend runs on `8000` internally

## 10. Troubleshooting

### Dispatch fails with 401/403

- Verify `CROSS_REPO_TOKEN` exists and has actions permissions.

### No repositories processed

- Check `config/repositories.yml` schema and names.
- Run `validate-config.yml` or local YAML validation.

### No dashboard updates

- Confirm workers call `/event` endpoint.
- Check frontend `NEXT_PUBLIC_WS_URL` and backend availability.

## 11. Migration Notes

- `matrix-codex` is the canonical package and CLI.
- `matrix-maintainer` alias remains for compatibility during migration.
