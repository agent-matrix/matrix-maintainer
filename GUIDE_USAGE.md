# GUIDE_USAGE — Agent‑Matrix Self‑Maintenance (first enterprise demo)

> The smallest **scalable** loop that proves the ecosystem: Agent‑Matrix
> maintains its own repositories using generic, reusable products —
> dry‑run safe, encrypted in transit, and observable from one console.
>
> **Pattern:** `matrix-maintainer (sender) → SelfRepair (control plane) →
> GitPilot (the coder) → models via OllaBridge, validation via MatrixLab →
> report + notification back in the console.`

---

## 1. What this is

A repository can be **onboarded once** and then checked **every day**: SelfRepair
diagnoses it, builds a repair plan, delegates the code change to **GitPilot**
(the default AI coder), validates in **MatrixLab**, and records the result. The
products are **generic** — Agent‑Matrix is simply the *first client*.

Live Spaces (all HTTPS):

| Component | URL | Role |
|---|---|---|
| OllaBridge Cloud | `ruslanmv-ollabridge.hf.space` | Inference gateway (OpenAI‑compatible). **Only holder of `HF_TOKEN`.** |
| GitPilot | `ruslanmv-gitpilot.hf.space` | AI coder. Bearer‑gated **coder API** `POST /repair`. |
| MatrixLab | `ruslanmv-matrixlab.hf.space` | Sandbox validation provider. |
| SelfRepair | `ruslanmv-selfrepair.hf.space` | **Control plane / system of record** + operator console. |
| matrix‑maintainer | this repo (GitHub Actions) | Agent‑Matrix **first client** — submits work to SelfRepair. |

---

## 2. Architecture & end‑to‑end workflow

```
  TRIGGERS
  ┌───────────────────────────┐         ┌───────────────────────────────┐
  │ matrix‑maintainer         │         │ Operator in the SelfRepair UI │
  │ • GitHub Actions daily cron│        │ • submit / view from console  │
  │ • matrix‑codex submit‑…    │        └───────────────┬───────────────┘
  └─────────────┬─────────────┘                         │
                │  POST /v1/plans  (Bearer SELFREPAIR_INGEST_TOKEN, HTTPS)
                │  {repo, mode:dry_run, client_id:"matrix‑maintainer"}
                ▼
  ╔═══════════════════════════════════════════════════════════════════════════════════╗
  ║  SelfRepair  ▸ CONTROL PLANE (system of record)                                     ║
  ║  intake ─▶ Message + Job(queued) + Notification("request received")  ── audited     ║
  ║     ▼  health worker (daemon thread, dry‑run, never writes the repo)                ║
  ║   1) ANALYZE  via GitHub REST API ─────────▶ api.github.com                         ║
  ║        detectors → health_score + issues (missing CI/tests/license/…)               ║
  ║   2) PLAN     → repair‑plan {issues, allowed_paths, forbidden_paths,                 ║
  ║                 coder:{provider:"gitpilot"}, sandbox:{matrixlab,…}}                  ║
  ║   3) DELEGATE to the coder (DEFAULT = GitPilot) ─────────┐                           ║
  ║                                                          │ POST /repair             ║
  ║                                                          │ (Bearer GITPILOT_TOKEN,  ║
  ║                                                          │  HTTPS, retry on 429)     ║
  ║                                                          ▼                           ║
  ║   4) RECORD job + report (+ patch preview) + Notification("report ready")           ║
  ╚════════════════════════════════╦════════════════════════╦═════════════════════════╝
        persists to                ║                        ║
   Neon Postgres · Upstash Redis   ║                        ▼
   · Mailtrap (email)              ║      ╔══════════════════════════════════════════╗
                                   ║      ║ GitPilot ▸ CODER API  POST /repair         ║
   shows in the console ◀──────────╝      ║   12‑step repair flow (dry‑run):           ║
   (Inbox · 🔔 bell · Audit)              ║   code‑fast → code‑coder → code‑reviewer   ║
                                          ║      │ models via OllaBridge               ║
                                          ║      │ sandbox via MatrixLab /repo/validate║
                                          ║      ▼ repair‑response {patch_preview,…}    ║
                                          ╚══════════════════════════════════════════╝
```

**Step by step**

1. **Submit** — matrix‑maintainer (cron or CLI), or the operator, sends a
   `maintenance_request` to `POST /v1/plans`.
2. **Analyze** — SelfRepair inspects the repo via the GitHub REST API (no clone)
   and computes `health_score` + an `issues` list.
3. **Plan** — issues become a `repair-plan` (allowed/forbidden paths,
   `coder.provider="gitpilot"`, sandbox profile).
4. **Delegate** — SelfRepair calls GitPilot's **bearer‑authenticated** coder API
   `POST /repair`; GitPilot runs `code-fast → code-coder → code-reviewer` (models
   through OllaBridge), validates in MatrixLab, and returns a **dry‑run patch
   preview**.
5. **Record** — SelfRepair stores the job + report and raises a "report ready"
   notification.
6. **Observe** — it all appears in the SelfRepair console (Inbox, 🔔 bell, Audit).

---

## 3. The SelfRepair console (single, unified UI)

```
  ruslanmv-selfrepair.hf.space   (one dark React "SelfRepair Console")
  ┌──────────────────────────────────────────────────────────────────────────┐
  │ Pre‑auth: Login · Register · Verify · Forgot · Reset  (email‑verified)     │
  │   └ after reset/verify → confirmation + auto‑redirect to sign‑in           │
  ├──────────────────────────────────────────────────────────────────────────┤
  │ Authenticated shell (sidebar + topbar 🔔 + ⌘K palette, mobile drawer)      │
  │   Operate:  Overview · Inbox (control‑plane requests) · Repos · Findings…  │
  │   Govern:   Policies · Audit log                                           │
  │   Configure:Connections (OllaBridge/GitPilot/MatrixLab — Save & Test)      │
  │   ADMIN (role‑gated, server‑enforced): Users · System · Logs              │
  │            └ ROOT superuser: created once, protected, grants admin         │
  └──────────────────────────────────────────────────────────────────────────┘
   State: Neon Postgres · Upstash Redis (tokens + rate limits) · Mailtrap (email)
```

---

## 4. How to use it

### A. As an operator (manual)
1. Open `https://ruslanmv-selfrepair.hf.space`, sign in (root: `contact@ruslanmv.com`).
2. **Connections** → confirm OllaBridge / GitPilot / MatrixLab, click **Test**.
3. Watch the **Inbox** + 🔔 **bell** as requests are processed; open a job to see
   the health report and the GitPilot patch preview.
4. **Admin → Users** to invite/manage users (root grants `admin`).

### B. Automated (matrix‑maintainer, daily)
- Onboard a repo: add one line to `config/repos.yml`.
- Submit on demand:
  ```bash
  matrix-codex submit-maintenance --repo agent-matrix/network.matrixhub --mode dry_run
  # or all inventory repos:
  matrix-codex submit-maintenance
  ```
- Daily cron: `.github/workflows/selfrepair-daily.yml` runs
  `scripts/submit_daily_maintenance.py` (pilot‑scoped to
  `agent-matrix/network.matrixhub`).

---

## 5. Configuration (secrets — names only; rotate regularly)

**SelfRepair Space:** `DATABASE_URL` (Neon), `UPSTASH_REDIS_REST_URL/TOKEN`,
`MAILTRAP_TOKEN`, `SELFREPAIR_SECRET_KEY`, `APP_BASE_URL`, `ADMIN_EMAIL/PASSWORD`,
`SELFREPAIR_INGEST_TOKEN` (+`SELFREPAIR_INGEST_CLIENT`), `GITPILOT_URL`,
`GITPILOT_TOKEN`, and (recommended) a read‑only `GITHUB_TOKEN`.

**GitPilot Space:** `GITPILOT_API_TOKEN` (enables the bearer‑gated coder API),
`GITPILOT_CODER_DEMO` (`true` = deterministic preview; `false` = real
model‑generated patches via OllaBridge).

**matrix‑maintainer (GitHub Actions secrets):** `SELFREPAIR_BASE_URL`,
`SELFREPAIR_INGEST_TOKEN` (must match the SelfRepair Space).

---

## 6. Security model (golden rules)

- **HTTPS everywhere** (HF terminates TLS) → tokens and payloads encrypted in transit.
- **Bearer auth** on machine paths: `SELFREPAIR_INGEST_TOKEN` (intake) and
  `GITPILOT_API_TOKEN` (coder); constant‑time comparison.
- **Only OllaBridge holds `HF_TOKEN`.** Everything else uses `ob_*` keys + URLs.
- **Dry‑run by default**, no real PRs, **fail‑closed** on empty/violated
  `allowed_paths`, and every action is **audited**.
- **RBAC:** `/v1/admin/*` → `403` for non‑admins; the **root** superuser is
  immutable (cannot be demoted, deactivated, or deleted).

---

## 7. Why it's scalable (enterprise‑ready foundation)

- **Generic products, not one‑offs** — OllaBridge / GitPilot / SelfRepair /
  MatrixLab are client‑agnostic; Agent‑Matrix is just `client_id`. New clients
  (orgs, CI, developers) reuse the same APIs.
- **Onboarding = one inventory line** — add repos to `config/repos.yml`; the
  daily cron picks them up automatically.
- **Pluggable coder, GitPilot by default** — the `coder.provider` abstraction
  lets you add coders later without replacing GitPilot.
- **Stateless, horizontally‑friendly backends** — Postgres for the system of
  record, Redis for ephemeral tokens/rate limits, model traffic centralized in
  OllaBridge (one place to manage cost, keys, and providers).
- **Observable + governed** — single console (Inbox, notifications, audit),
  server‑enforced RBAC, dry‑run + path policy — the controls enterprises expect.

---

## 8. Status: live vs. one‑flag activation

- **Live & verified:** all four Spaces; the full loop end‑to‑end with a real
  dry‑run patch preview; bearer‑gated coder API (`401` without token, `200`
  with); email‑verified auth + admin/root; mobile‑responsive UI.
- **One flag each to scale up:**
  - real patches → `GITPILOT_CODER_DEMO=false` (GitPilot Space).
  - reliable daily analysis → set a read‑only `GITHUB_TOKEN` (SelfRepair Space).
  - automatic daily runs → add the two GitHub Actions secrets above.

---

## 9. Quick verification

```bash
# health of the control plane
curl -s https://ruslanmv-selfrepair.hf.space/health        # db/redis/email all true

# coder API is bearer‑gated
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  https://ruslanmv-gitpilot.hf.space/repair -d '{}'         # 401 without a token

# submit one maintenance request (machine client)
curl -s -X POST https://ruslanmv-selfrepair.hf.space/v1/plans \
  -H "Authorization: Bearer $SELFREPAIR_INGEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"maintenance_request","repo_url":"https://github.com/agent-matrix/network.matrixhub","mode":"dry_run","client_id":"matrix-maintainer"}'
# → then watch the Inbox / 🔔 bell in the console for the report + patch preview
```
