# Matrix Codex <img src="status-site/assets/logo.svg" alt="Matrix Codex" width="30" />

<p>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/GitHub%20Actions-Orchestration-2088FF?logo=githubactions&logoColor=white" alt="GitHub Actions" />
  <img src="https://img.shields.io/badge/Architecture-Controller%20%2B%20Workers-6f42c1" alt="Architecture" />
  <img src="https://img.shields.io/badge/License-Apache--2.0-brightgreen" alt="License" />
</p>

> **Autonomous maintenance control plane for multi-repository engineering systems.**

Matrix Codex is designed to keep repositories healthy with a governed loop:
**discover → scan → plan → approve → execute → verify → report**.

---

## 🚀 Why Matrix Codex

- ✅ **Scalable maintenance** across many repositories.
- ✅ **Safe by default** with policy + approval + PR-first boundaries.
- ✅ **Agent-ready** architecture for Codex/GitPilot/Ollama-style executors.
- ✅ **Observable** via status APIs, state snapshots, and dashboard artifacts.
- ✅ **Extensible** task engine and profile-based command system.

---

## 🧠 System architecture (improved)

```mermaid
flowchart TB
    subgraph Inputs["📥 Inputs"]
      A1[Repository Inventory\nconfig/repositories.yml]
      A2[Policies\nconfig/policies.yml]
      A3[Task Rules\nconfig/tasks.yml]
    end

    subgraph ControlPlane["🧭 Matrix Codex Control Plane"]
      B1[🩺 Health Scanner]
      B2[🧩 Task Engine]
      B3[🛡️ Guardian + 💰 Treasury Checks]
      B4[🚀 Dispatcher]
      B5[🗃️ StorageDB\nRuns / Tasks / Events]
    end

    subgraph Workers["🛠️ Repo Workers (GitHub Actions)"]
      C1[GitPilot / Codex / Ollama Agents]
      C2[Install • Lint • Test • Fix]
      C3[PR Creation / Update]
    end

    subgraph Outputs["📊 Outputs"]
      D1[Status API /maintainer/*]
      D2[Dashboard + Static Site]
      D3[Audit Trail in state/]
    end

    A1 --> B1
    A2 --> B3
    A3 --> B2
    B1 --> B2 --> B3 --> B4
    B4 --> C1 --> C2 --> C3
    C2 --> B5
    C3 --> B5
    B5 --> D1 --> D2
    B5 --> D3
```

### Loop in one sentence
Matrix Codex scans health issues, converts them into constrained tasks, checks safety/budget, dispatches repo-local workers, and records outcomes for continuous improvement.

---

## 📦 Repository map

### Core controller
- `matrix_codex/main.py` → orchestration loop (`scan`, `plan`, `run`, `report`)
- `matrix_codex/health_scanner.py` → issue detection
- `matrix_codex/task_engine.py` → issue-to-task mapping
- `matrix_codex/orchestration/dispatcher.py` → cross-repo workflow dispatch
- `matrix_codex/storage/models.py` → run/task/event persistence

### API + status
- `apps/backend/main.py` → backend status/event service
- `matrix_codex/api/routes.py` → maintainer API (`/maintainer/runs`, `/tasks`, `/events`, `/health_scans`)

### Worker orchestration
- `.github/workflows/matrix-maintainer-orchestrator.yml` → scheduled controller run
- `matrix_codex/worker_templates/matrix-maintainer.yml` → target repo worker template

---

## ⚙️ Installation

```bash
make install
```

Fallback:

```bash
uv sync
```

If your environment blocks external package download, use pre-installed dependencies and run commands with `PYTHONPATH=.`.

---

## 🔐 Configuration

Edit these files first:

- `config/repositories.yml` → repositories, profiles, commands
- `config/policies.yml` → risk and path restrictions
- `config/tasks.yml` → issue→task behavior per repo

Common environment variables:

- `GITHUB_TOKEN`, `CROSS_REPO_TOKEN`
- `WORKER_WORKFLOW_FILE`
- `GITPILOT_MODE`, `GITPILOT_PROVIDER`
- `MATRIX_CODEX_EXECUTION_MODE`

---

## 🧪 Usage

### End-to-end manual run

```bash
matrix-codex scan-health
matrix-codex plan-maintenance
matrix-codex run-maintenance
matrix-codex report-status
```

### Full daily run

```bash
make run-daily
```

### Tests

```bash
make test
```

---

## 🤖 Compatibility status (verified from repo implementation)

| Platform | Status | Notes |
|---|---|---|
| **Ollama** | 🟡 Partial | `app/agents/ollama_agent.py` exists but currently returns `not_implemented` placeholder. |
| **OllamaBridge** | 🟡 Planned | No dedicated `ollamabridge` adapter currently present in codebase; add bridge client module to enable runtime integration. |
| **Hugging Face Spaces** | 🟢 Supported | Workflow `.github/workflows/sync-matrix-codex-status-to-hf-space.yml` deploys backend/frontend bundle to HF Space. |

For details and rollout checklist, see `docs/compatibility.md`.

---

## 📡 API endpoints

- `GET /health`
- `GET /status`
- `POST /event`
- `WS /ws`
- `GET /maintainer/runs`
- `GET /maintainer/tasks`
- `GET /maintainer/events`
- `GET /maintainer/health_scans`

---

## 📚 Documentation

- `docs/technical-guide.md` — technical setup and internals
- `docs/architecture.md` — architecture notes
- `docs/ai-maintainer-guide.md` — AI handoff and extension guide
- `docs/usage.md` — quick usage walkthrough
- `docs/compatibility.md` — Ollama / OllamaBridge / Hugging Face compatibility matrix

---

## 🧰 Best practices for maintainability

1. Keep tasks small and policy-safe.
2. Prefer PR-only automation.
3. Add tests for every new scanner/task rule.
4. Keep profile commands explicit and reproducible.
5. Record failures clearly in event payloads and PR notes.

---

## 📄 License

Apache-2.0
