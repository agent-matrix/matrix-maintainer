# Matrix Codex <img src="status-site/assets/logo.svg" alt="Matrix Codex logo" width="28" />

<div align="left">

![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automation-2088FF?logo=githubactions&logoColor=white)
![Status](https://img.shields.io/badge/Mode-Controller%20%2B%20Workers-6f42c1)
![License](https://img.shields.io/badge/license-Apache--2.0-brightgreen)

</div>

**Matrix Codex** is an autonomous repository-maintenance control plane for the Agent‑Matrix ecosystem.
It scans repo health, plans maintenance work, applies governance and budget checks, dispatches worker runs, and publishes status artifacts.

---

## ✨ What this project does

- 🧭 **Discovers repositories** and keeps an inventory.
- 🩺 **Scans health signals** (CI/test/dependency/lint indicators).
- 🧠 **Builds maintenance tasks** from issues with policy-aware defaults.
- 🛡️ **Applies governance checks** (risk, allowed paths, PR-only boundaries).
- 🚀 **Dispatches worker workflows** into target repositories.
- 📊 **Persists and reports outcomes** through APIs + static status site.

---

## 🧩 How it works (simple diagram)

```mermaid
flowchart LR
    A[Repository Inventory] --> B[Health Scanner]
    B --> C[Task Engine]
    C --> D[Guardian + Treasury checks]
    D --> E[GitPilot/Worker Dispatch]
    E --> F[Events + Run Storage]
    F --> G[Status API + Dashboard]
```

### Runtime loop

1. `scan-health`
2. `plan-maintenance`
3. `run-maintenance`
4. `report-status`

The scheduled orchestrator executes this same sequence daily.

---


## 🧠 Matrix Maintainer Foundation

This repository now also ships a `matrix-maintainer` foundation under `app/` with:

- FastAPI service (`app/main.py`)
- SQLAlchemy models for repositories/runs/events (`app/db/models.py`)
- Dispatch + scheduler loop (`app/control/dispatcher.py`, `app/control/scheduler.py`)
- Pluggable agents (Codex, GitPilot, Ollama) (`app/agents/`)
- Guardian/Treasury adapters for policy and budget enforcement (`app/policy`, `app/economy`)

Run locally:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 📁 Repository Structure

```text
matrix-codex/
├── matrix_codex/                     # Python controller package
├── app/                              # Matrix Maintainer API/control-plane foundation
├── config/repositories.yml           # Legacy inventory for matrix-codex
├── config/repos.yml                  # Matrix Maintainer repo inventory
├── config/policies.yml               # Matrix Maintainer guardrails
├── scripts/                          # Dispatch/report helper scripts
├── .github/workflows/                # Orchestrator + validation workflows
├── target-repo-template/             # Worker template for managed repos
├── apps/backend/                     # FastAPI status backend
├── apps/frontend/                    # Next.js status dashboard
├── state/                            # Status/history artifacts
└── docs/                             # Technical documentation
```

### Controller plane (this repository)

- `matrix_codex/health_scanner.py` — detection engine
- `matrix_codex/task_engine.py` — issue → task mapping
- `matrix_codex/main.py` — orchestration loop
- `matrix_codex/orchestration/dispatcher.py` — cross-repo workflow dispatch
- `matrix_codex/storage/models.py` — persistent run/task/event storage

### Service & API

- `apps/backend/main.py` — status/event backend
- `matrix_codex/api/routes.py` — maintainer API routes (`/maintainer/*`)

### Worker side

- `.github/workflows/matrix-maintainer-orchestrator.yml` — controller scheduler
- `matrix_codex/worker_templates/matrix-maintainer.yml` — target repo worker template

---

## ⚙️ Installation

### Option A — recommended

```bash
make install
```

### Option B — direct

```bash
uv sync
```

> If your environment blocks external network access, dependency fetch may fail. In that case use the preinstalled environment and run local commands with `PYTHONPATH=.`.

---

## 🔐 Configuration

Main configuration files:

- `config/repositories.yml` → repo catalog + execution profiles
- `config/policies.yml` → safety boundaries and risk thresholds
- `config/tasks.yml` → health issue → maintenance task behavior

Useful environment variables:

- `GITHUB_TOKEN` / `CROSS_REPO_TOKEN`
- `WORKER_WORKFLOW_FILE`
- `MATRIX_CODEX_EXECUTION_MODE`
- `GITPILOT_MODE`, `GITPILOT_PROVIDER`

---

## 🚀 Usage

### Daily automation

```bash
make run-daily
```

### Manual step-by-step

```bash
matrix-codex scan-health
matrix-codex plan-maintenance
matrix-codex run-maintenance
matrix-codex report-status
```

### Local checks

```bash
make test
```

---

## 🧪 Developer commands

```bash
make install
make test
make lint
make build-site
```

---

## 📡 Status and observability

- API health: `GET /health`
- Controller status: `GET /status`
- Maintainer records: `/maintainer/runs`, `/maintainer/tasks`, `/maintainer/events`, `/maintainer/health_scans`
- WebSocket stream: `WS /ws`

---

## 📚 Documentation

- **Technical guide**: `docs/technical-guide.md`
- Architecture notes: `docs/architecture.md`
- AI maintainer guide: `docs/ai-maintainer-guide.md`
- Governance and operations docs: `docs/`

---

## 📄 License

Apache-2.0
