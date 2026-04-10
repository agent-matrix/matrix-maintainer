# 🚀 Matrix Codex

> **Enterprise orchestration platform for repository maintenance at scale.**

`matrix-codex` is the central controller for managing maintenance across many repositories.  
It discovers repositories, plans operations, dispatches worker runs, collects outcomes, and publishes status.

---

## ✨ What You Get

- 🧭 **Central Control Plane**: one place to operate all managed repositories.
- 🤖 **Codex-Driven Operations**: reusable operation profiles for maintenance, linting, test repair, and upgrades.
- 🔁 **Worker-Based Execution**: each target repository runs changes in its own CI context (safer, isolated).
- 📊 **Status & Observability**: API + dashboard for repo health and action history.
- 🧾 **Auditability**: JSON state artifacts and workflow logs for traceability.

---

## 🏗️ Architecture Overview

`matrix-codex` follows a controller/worker model:

1. **Controller** (this repo)
   - Reads repo inventory (`config/repositories.yml`)
   - Selects operation and target repos
   - Dispatches target worker workflows
   - Aggregates results

2. **Worker** (in each target repo)
   - Executes operation in local repo context
   - Runs validation/tests
   - Commits and opens PR when needed

3. **Reporter / Dashboard**
   - Publishes status snapshots
   - Exposes API (`/status`, `/event`, `/ws`)
   - Renders live status UI

---

## 📁 Repository Structure

```text
matrix-codex/
├── matrix_codex/                     # Python controller package
├── config/repositories.yml           # Repo inventory
├── config/profiles.yml               # Validation profiles by stack
├── scripts/                          # Dispatch/report helper scripts
├── .github/workflows/                # Orchestrator + validation workflows
├── target-repo-template/             # Worker template for managed repos
├── apps/backend/                     # FastAPI status backend
├── apps/frontend/                    # Next.js status dashboard
├── state/                            # Status/history artifacts
└── docs/                             # Technical documentation
```

---

## ⚙️ Quick Start

### 1) Install dependencies

```bash
uv sync
```

### 2) Run key commands

```bash
matrix-codex discover
matrix-codex run-daily
matrix-codex check-repo agent-matrix/matrix-hub
matrix-codex publish-site
```

### 3) Run local status dashboard (optional)

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend status API: `http://localhost:8000/status`

---

## 🔐 Required Credentials

For orchestration against GitHub:

- `GITHUB_TOKEN` (or)
- `CROSS_REPO_TOKEN` ✅ recommended for cross-repo dispatch

Token should have access to:

- repository contents
- Actions (dispatch workflows)
- pull requests (if opening PRs)

See **docs technical guide** for complete credential setup.

---

## 🧪 Operational Workflows

- `orchestrate-agent-matrix.yml`: dispatch operation across fleet
- `daily-orchestrator.yml`: scheduled daily orchestration
- `manual-orchestrator.yml`: manual dispatch/local fallback
- `validate-config.yml`: schema checks for inventory config
- `rollout-worker-template.yml`: preview worker-template rollout plan

---

## 📡 Status Dashboard API

FastAPI backend (`apps/backend/main.py`) exposes:

- `GET /health`
- `GET /status`
- `POST /event`
- `WS /ws`

Example event:

```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"repo":"matrix-ai","status":"running"}'
```

---

## 🧰 Best Practices

- ✅ Keep controller logic centralized, execution decentralized.
- ✅ Prefer PR-based changes over direct pushes.
- ✅ Use per-repo profiles for safe defaults.
- ✅ Roll out to pilot repos first, then scale.
- ✅ Track every run with artifacts and dashboard history.

---

## 📚 Documentation

- **Technical guide**: `docs/technical-guide.md`
- Architecture notes: `docs/architecture.md`
- Governance and operations docs: `docs/`

---

## 🤝 Compatibility

`matrix-codex` is the primary CLI.  
`matrix-maintainer` remains available as a compatibility alias during migration.


---

## 🛠️ Automation Hardening

Recent reliability upgrades included:

- standardized dispatch workflow name to `matrix-codex-worker.yml`
- worker template now uses Codex action (`openai/codex-action@v1`)
- worker lifecycle status callbacks (`running/success/failed`) to dashboard API
- persistent backend state at `state/runtime_status.json`
- profile-based validation runner (`matrix_codex.execution.worker_runner`)


## 🌍 Environment Setup (Local + GitHub)

### Local `.env`

Create a `.env` file in the repository root:

```env
GITHUB_ORG=agent-matrix
GITHUB_BASE_BRANCH=main
MATRIX_CODEX_EXECUTION_MODE=dispatch
MATRIX_CODEX_OPERATION=daily-maintenance
```

Optional local API wiring for dashboard development:

```env
BACKEND_STATUS_URL=http://127.0.0.1:8000/status
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000/ws
```

### GitHub Secrets (required for automation)

Set these in **Repository** or **Organization** Secrets (`Settings → Secrets and variables → Actions`):

- `OPENAI_API_KEY` → required for `openai/codex-action@v1`
- `CROSS_REPO_TOKEN` → required for cross-repo workflow dispatch
- `STATUS_API_URL` → optional; enables worker lifecycle callbacks to dashboard API

### Codex worker step reference

```yaml
- name: Codex operation
  uses: openai/codex-action@v1
  with:
    api-key: ${{ secrets.OPENAI_API_KEY }}
    prompt: >-
      Apply operation safely and keep diffs minimal.
```


## 🤗 Hugging Face Space Deployment (Backend + Frontend)

This repository includes a deployment workflow for a Docker Space:

- Workflow: `.github/workflows/sync-matrix-codex-status-to-hf-space.yml`
- Space metadata template: `deploy/huggingface/README.md`

### Required GitHub Secrets

- `HF_TOKEN` (write access to Spaces)
- `HF_USERNAME` (your HF username)
- `SPACE_NAME` (target Space repo name)

The workflow builds a clean deploy tree from `apps/backend`, `apps/frontend`, and `Dockerfile`, then force-pushes it to your HF Space.

#### What is `SPACE_NAME`?

Use the **Space slug only** (not the full URL):

- Space URL: `https://huggingface.co/spaces/your-user/matrix-codex-status`
- `HF_USERNAME=your-user`
- `SPACE_NAME=matrix-codex-status`

