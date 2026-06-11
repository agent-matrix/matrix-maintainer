# First-wave local repair stack (MVP-001)

The smallest working loop of the Agent-Matrix ecosystem, on one machine.

```text
OllaBridge API key
  → SelfRepair creates repair-plan.json
    → GitPilot generates a patch in dry-run
      → MatrixLab validates the patch
        → Matrix Maintainer records the first maintenance run
```

Matrix Maintainer is the **first client** here — it consumes the generic
products (OllaBridge, SelfRepair, GitPilot, MatrixLab), it is not baked into
them.

## Services

| Service          | Port | Role                                           |
|------------------|------|------------------------------------------------|
| `ollabridge-cloud` | 8000 | Generic inference gateway. **Only** holder of `HF_TOKEN`. |
| `matrixlab`      | 8765 | Generic sandbox validation provider.           |
| `gitpilot`       | 9000 | Generic AI coder (writes patches, dry-run).    |
| `selfrepair`     | 9100 | Repo maintenance/admin (plans, never writes code). |

## Prerequisites

Check the product repos out as **siblings** of `matrix-maintainer`:

```text
<workspace>/
  ollabridge-cloud/
  matrixlab/
  gitpilot/
  SelfRepair/
  matrix-maintainer/   <- you are here
```

If your layout differs, set the `*_CONTEXT` overrides in `.env`.

## Bring it up

```bash
cd deploy/local-repair-stack
cp .env.example .env          # optionally add a real HF_TOKEN
docker compose up --build
```

`HF_TOKEN` is optional: leave it blank and the whole stack runs offline with
OllaBridge's deterministic stub provider — enough to prove the loop.

## Definition of done

```bash
# 1. Health of the generic gateway and sandbox
curl http://localhost:8000/v1/health
curl http://localhost:8765/health
curl http://localhost:9000/v1/health
curl http://localhost:9100/v1/health

# 2. OllaBridge issues a usable, OpenAI-compatible completion
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer ob_test_agentmatrix_xxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"code-coder","messages":[{"role":"user","content":"Write a minimal pytest health check."}]}'

# 3. SelfRepair builds a repair plan
selfrepair-repo plan https://github.com/agent-matrix/test-repair-target \
  --output repair-plan.json

# 4. GitPilot reads the plan and produces a patch preview (no PR)
gitpilot repair \
  --repo https://github.com/agent-matrix/test-repair-target \
  --plan repair-plan.json \
  --sandbox matrixlab \
  --dry-run

# 5. SelfRepair full dry-run (calls GitPilot + MatrixLab, writes report.json/md)
selfrepair-repo repair https://github.com/agent-matrix/test-repair-target \
  --coder gitpilot --sandbox matrixlab --dry-run

# 6. Matrix Maintainer records one complete run
matrix-codex scan-health
matrix-codex plan-maintenance
matrix-codex run-maintenance
matrix-codex report-status
```

Expected: `repair-plan.json` created, a patch preview generated, MatrixLab
validation logs returned, `report.json` / `report.md` written, one maintenance
run recorded — **no real PR**, and **no `HF_TOKEN` outside OllaBridge**.

## Safety

- Public/local default is **dry-run**: GitPilot never opens a real PR
  (`GITPILOT_DRAFT_PR_ENABLED=false`) and MatrixLab stubs execution
  (`MATRIXLAB_DRY_RUN=1`).
- Real PR creation and real sandbox execution require explicit configuration
  and are out of scope for the first wave.
