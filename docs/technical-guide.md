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
| `OPENAI_API_KEY` | required in CI worker | Runs Codex in GitHub Actions |
| `STATUS_API_URL` | optional | Worker callback endpoint for dashboard events |
| `GITHUB_ORG` | optional | Default org override |
| `MATRIX_CODEX_EXECUTION_MODE` | optional | `dispatch` (default) or `local` |
| `MATRIX_CODEX_OPERATION` | optional | operation name for runs |


### `.env` starter template

```env
GITHUB_ORG=agent-matrix
GITHUB_BASE_BRANCH=main
MATRIX_CODEX_EXECUTION_MODE=dispatch
MATRIX_CODEX_OPERATION=daily-maintenance
```

For local dashboard development:

```env
BACKEND_STATUS_URL=http://127.0.0.1:8000/status
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000/ws
```

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



### GitHub Actions secret setup

1. Go to: `Settings → Secrets and variables → Actions`.
2. Add secrets:
   - `OPENAI_API_KEY`
   - `CROSS_REPO_TOKEN`
   - `STATUS_API_URL` (optional)

### Codex action usage

```yaml
- name: Codex operation
  uses: openai/codex-action@v1
  with:
    api-key: ${{ secrets.OPENAI_API_KEY }}
    prompt: >-
      Apply operation safely, run validation, and keep changes minimal.
```

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



### Hugging Face Space sync workflow

File: `.github/workflows/sync-matrix-codex-status-to-hf-space.yml`

This workflow:

1. Validates `HF_TOKEN`, `HF_USERNAME`, and `SPACE_NAME` secrets.
2. Builds a clean deploy tree containing:
   - `apps/backend`
   - `apps/frontend`
   - `Dockerfile`
   - `README.md` (from `deploy/huggingface/README.md`)
3. Force-pushes that deploy tree to your Hugging Face Space repository.

Required secrets:

- `HF_TOKEN`
- `HF_USERNAME`
- `SPACE_NAME`


`SPACE_NAME` is the Hugging Face Space slug (the repo name after username), not a full URL.

Example:

- URL: `https://huggingface.co/spaces/your-user/matrix-codex-status`
- `HF_USERNAME=your-user`
- `SPACE_NAME=matrix-codex-status`

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
