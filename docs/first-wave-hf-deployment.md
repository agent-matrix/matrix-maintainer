# First-wave Hugging Face deployment (MVP-001)

How to deploy the first-wave products to Hugging Face Spaces efficiently.
Backend APIs run on **CPU/Docker** Spaces. **ZeroGPU is never used for
backend APIs** — only for GPU-heavy Gradio demo functions, which are out of
scope for the first wave.

## OllaBridge Cloud Space

- **SDK:** Docker
- **Hardware:** CPU Basic
- **Secrets:** `HF_TOKEN`, `OLLAMBRIDGE_MASTER_KEY`
- Do not expose real keys in logs (the audit log masks them).
- OllaBridge is the **only** Space that receives `HF_TOKEN`.

## GitPilot Demo Space

- **SDK:** Docker (or Gradio for a thin UI)
- **Hardware:** CPU Basic
- **Mode:** dry-run only (`GITPILOT_DEMO_MODE=true`, `GITPILOT_DRAFT_PR_ENABLED=false`)
- **Secrets:**
  - `OPENAI_BASE_URL=https://<ollabridge-space>.hf.space/v1`
  - `OPENAI_API_KEY=ob_test_gitpilot_xxx`
- No `HF_TOKEN` here.

## SelfRepair Admin Demo Space

- **SDK:** Docker
- **Hardware:** CPU Basic
- **Mode:** public repos only, dry-run only
- **Secrets:**
  - `OPENAI_BASE_URL=https://<ollabridge-space>.hf.space/v1`
  - `OPENAI_API_KEY=ob_test_selfrepair_xxx`
  - `GITPILOT_URL=https://<gitpilot-space>.hf.space`
  - `MATRIXLAB_URL=https://<matrixlab-space>.hf.space`

## MatrixLab Space

- **SDK:** Docker
- **Hardware:** CPU Basic
- **Mode:** stub/dry-run execution for public demos (`MATRIXLAB_DRY_RUN=1`).

## ZeroGPU policy

Do **not** use ZeroGPU for OllaBridge, GitPilot, SelfRepair, or MatrixLab.
ZeroGPU is reserved for later GPU-heavy Gradio demos (e.g. `medos-demo`,
`homepilot-avatar-demo`, a future `matrixlab-gpu-sandbox-demo`). When a Space
genuinely needs a GPU, wrap only the GPU-dependent function:

```python
import spaces

@spaces.GPU(duration=60)
def generate(...):
    ...
```

Request `xlarge` (96 GB VRAM) only when the workload truly needs it — it costs
double quota and can increase queueing.
