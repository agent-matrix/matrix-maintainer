# Matrix-Maintainer — Orchestration Design

> Status: draft for review
> Owner: agent-matrix
> Scope: design only; no code changes in this commit
> Companion to: `docs/architecture.md`, `docs/ai-maintainer-guide.md`

This document audits the current state of `agent-matrix/matrix-maintainer`
against the executive plan, defines clear boundaries with SelfRepair,
GitPilot, MatrixHub, and OllaBridge, identifies gaps, and proposes a
phased roadmap using industry best-practice patterns.

---

## 1. TL;DR

1. The repo `agent-matrix/matrix-maintainer` **already exists** and is
   ~60–70% built. Internally it is named **Matrix Codex** (package
   `matrix_codex`, CLI `matrix-codex`). The executive plan’s product
   brand is **Matrix Maintainer**. This brand/package mismatch must be
   reconciled before public release.
2. SelfRepair already implements most of what the plan calls the
   "scanner + healer + reporter" engine — including multi-platform
   discovery (GitHub/GitLab/HF), analyzers, fixers, governance, CI
   guardian, OllaBridge LLM, sandbox, and a static status site.
   Matrix-Maintainer **must not re-implement these**. It should call
   SelfRepair via a stable client adapter.
3. The orchestration loop (`scan → plan → approve → budget → execute →
   reconcile`) exists and is wired to GitHub Actions worker dispatch.
   What is missing is **the second product surface**: MCP-server
   discovery, verification, tagging, patch storage and patch-on-install.
4. Recommended next move: keep the existing orchestrator, treat
   "Matrix Codex" as the engine codename and "Matrix Maintainer" as the
   product, expose a stable `matrix-maintainer` CLI alias, **wire
   SelfRepair as a first-class adapter**, and build MVP-2 (MCP
   verification) and MVP-3 (patch archive) as net-new modules.

---

## 2. Current state audit (what is already here)

Cross-walk between the executive plan’s proposed structure and what
exists today in this repo.

| Plan module                             | Current location                                             | Status                          |
| --------------------------------------- | ------------------------------------------------------------ | ------------------------------- |
| `cli.py`                                | `matrix_codex/cli.py` (Typer; entry `matrix-codex`)          | Present, but wrong CLI name     |
| `config/settings.py`                    | `matrix_codex/settings.py` + `config/*.yml`                  | Present                         |
| `inventory/github_org.py`               | `matrix_codex/inventory/org_discovery.py`                    | Present (GitHub only)           |
| `inventory/mcp_discovery.py`            | —                                                            | **Missing**                     |
| `orchestrator/pipeline.py`              | `matrix_codex/main.py`                                       | Present (scan→plan→run→report)  |
| `orchestrator/scheduler.py`             | `.github/workflows/matrix-maintainer-orchestrator.yml`       | Present (GH-Actions cron)       |
| `orchestrator/job_runner.py`            | `matrix_codex/orchestration/dispatcher.py`                   | Present (worker dispatch)       |
| `selfrepair/client.py`                  | `app/agents/*` and partial `matrix_codex/healing/`           | **Partial / overlapping**       |
| `gitpilot/client.py`                    | `matrix_codex/gitpilot/runner.py`, `app/agents/gitpilot.py`  | Present                         |
| `verifier/sandbox.py`                   | `matrix_codex/matrixlab/` (delegated to MatrixLab)           | Present (thin)                  |
| `verifier/install_check.py`             | `cli.py:check_make` runs `make install test`                 | Present (workflow runtime)      |
| `patches/`                              | —                                                            | **Missing**                     |
| `storage/local.py`                      | `matrix_codex/storage/models.py` (JSON `StorageDB`)          | Present                         |
| `storage/github.py`                     | —                                                            | **Missing**                     |
| `storage/huggingface.py`                | —                                                            | **Missing**                     |
| `storage/cloudflare_r2.py`              | —                                                            | **Missing**                     |
| `matrixhub/publisher.py`                | `matrix_codex/agent_matrix/init.py` (Hub event publish)      | **Partial** (events only)       |
| `matrixhub/manifest_update.py`          | —                                                            | **Missing**                     |
| `matrixhub/status_badges.py`            | `matrix_codex/site/generator.py` (own dashboard)             | **Partial / wrong target**      |
| `policies/license_policy.py`            | `app/policy/`, `matrix_codex/governance/`, `config/policies.yml` | Present                     |
| `policies/risk_policy.py`               | `matrix_codex/governance/`                                   | Present                         |
| `policies/approval_policy.py`           | `app/policy/` (Guardian adapter)                             | Present                         |
| `reports/html_report.py`                | `matrix_codex/site/generator.py`, `apps/frontend/`           | Present                         |
| `reports/json_report.py`                | `matrix_codex/reporting/`                                    | Present                         |
| `reports/audit_log.py`                  | `state/maintainer_records.json` via `StorageDB`              | Present (basic)                 |

**Bottom line**: the orchestration spine and the agent-repo (workflow B
of the plan) for the Agent-Matrix org is largely in place. The MCP
maintenance surface, patch archive, and SelfRepair-as-client adapter
are the real gaps.

---

## 3. Reconciliation problem #1 — naming

The plan’s "core product sentence" puts **Matrix Maintainer** as the
brand. The current repo ships:

- Repo:    `agent-matrix/matrix-maintainer`     ✔ matches plan
- Package: `matrix_codex`                       ✘ does not match
- CLI:     `matrix-codex`                       ✘ does not match
- Docs and README use both names interchangeably

**Recommendation (low cost, high clarity)**:

1. Keep `matrix_codex` as the **internal codename** of the engine
   (think "Linux kernel" vs "Ubuntu" — Codex is the kernel, Maintainer
   is the distribution). Document this once, then stop switching.
2. Add a **`matrix-maintainer` CLI alias** as a second console-script
   entry-point in `pyproject.toml` that points to the same Typer app.
   This is one line; it gives users the branded CLI without a rename.
3. Rename the **distribution package on PyPI** to `matrix-maintainer`
   and keep `matrix_codex` as the import name. Both exist in the wild
   (e.g. `Pillow` distributes the `PIL` import).
4. Sweep the README/docs to lead with "Matrix Maintainer" as the
   product and mention Codex only when discussing the engine internals.

A full rename (`matrix_codex` → `matrix_maintainer`) is also possible,
but it touches every import in the repo and breaks any external
consumers. **Defer that** until a real reason emerges.

---

## 4. Reconciliation problem #2 — boundary with SelfRepair

This is the most important architectural decision in the project.

SelfRepair (ruslanmv/SelfRepair) already implements, with substantial
depth: inventory (GitHub/GitLab/HF), analyzers, standard checks,
healing loop, fix strategies, governance/policy, CI guardian, issue
watch, OllaBridge LLM assist, MatrixLab sandbox, reporting, static
status site, `/v1/rpc` agent endpoint.

`matrix_codex` independently re-implements a thin slice of the same
surface (`inventory/`, `analyzers/`, `health_scanner.py`, `healing/`,
`governance/`, `reporting/`, `site/`). Today these two stacks
**duplicate** logic with no contract between them.

The plan says SelfRepair = engine, Matrix-Maintainer = orchestrator.
That is the right call. Concretely:

**Define a single SelfRepair Client contract** that Matrix-Maintainer
depends on. Everything Matrix-Maintainer needs from SelfRepair goes
through this client; nothing else.

```python
# matrix_codex/selfrepair/client.py   (new)
class SelfRepairClient(Protocol):
    def scan(self, repo: RepoRef, *, profile: str | None = None) -> RepoHealthReport: ...
    def repair(self, repo: RepoRef, issues: list[HealthIssue], *, safe_only: bool) -> RepairResult: ...
    def validate(self, repo: RepoRef, *, in_sandbox: bool = True) -> ValidationReport: ...
    def report(self, repo: RepoRef) -> JsonReport: ...
```

Two implementations live behind it:

1. **`SelfRepairHttpClient`** — calls SelfRepair’s FastAPI service
   over the network. Used in production.
2. **`SelfRepairLocalClient`** — imports SelfRepair as a library and
   runs in-process. Used in CI and local dev.

After this is wired:

- Delete or quarantine the duplicated scanner/analyzer/healing code in
  `matrix_codex/` (mark deprecated for one release, then remove).
- All MM modules talk to SelfRepair via the client only.
- SelfRepair stays usable standalone outside Agent-Matrix — which is a
  stated goal.

The boundary, restated:

| Concern                                  | SelfRepair | GitPilot | Matrix-Maintainer | MatrixHub |
| ---------------------------------------- | :--------: | :------: | :---------------: | :-------: |
| Scan repository health                   | ✔          |          |                   |           |
| Apply deterministic safe fixes           | ✔          |          |                   |           |
| Sandbox install + test                   | ✔          |          |                   |           |
| Plan a complex code change               |            | ✔        |                   |           |
| Edit code via LLM, iterate on tests      |            | ✔        |                   |           |
| Decide *which* repo to act on, *when*    |            |          | ✔                 |           |
| Route an issue to SelfRepair or GitPilot |            |          | ✔                 |           |
| Open PR, attach reports                  |            |          | ✔                 |           |
| Store patches + manifests                |            |          | ✔                 |           |
| Publish trust + status badges            |            |          |                   | ✔         |
| Serve install metadata to clients        |            |          |                   | ✔         |

---

## 5. Reconciliation problem #3 — two FastAPI services

The repo currently has two FastAPI surfaces:

- `apps/backend/main.py` — Matrix Codex status/event backend.
- `app/main.py` — newer Matrix Maintainer foundation (db, scheduler,
  dispatcher, agents, policy, economy).

This split is confusing and will rot. Pick one and merge the other in.

**Recommendation**: promote `app/` as the new home (it has cleaner
SQLAlchemy models, proper scheduler, pluggable agent registry). Move
`apps/backend/` route handlers into `app/api/` and delete the duplicate
service. Keep `apps/frontend/` (Next.js dashboard) as the only UI.

---

## 6. The two product surfaces

The executive plan defines two distinct workflows. Treating them as two
**products on the same control plane** keeps the architecture clean.

### 6.1 Surface A — Agent-Matrix repo maintenance (mostly built)

End state (mostly already shipped):

```text
matrix-maintainer scan-org agent-matrix --report-only
matrix-maintainer repair-repo agent-matrix/matrix-hub --safe-only
matrix-maintainer repair-org agent-matrix --open-draft-pr
matrix-maintainer repair-org agent-matrix --use-gitpilot --open-draft-pr
```

Gap list to call this surface "done":

1. Rename CLI to `matrix-maintainer` (alias is fine).
2. `scan-org` / `repair-org` / `repair-repo` subcommands as friendly
   wrappers over the existing `scan-health` / `plan-maintenance` /
   `run-maintenance` chain.
3. Replace duplicated scanner with `SelfRepairClient`.
4. `--report-only`, `--safe-only`, `--use-gitpilot`, `--open-draft-pr`
   flags wired to policy decisions instead of separate code paths.
5. PR body templating with attached SelfRepair JSON + HTML report.

### 6.2 Surface B — MCP server verification (net-new)

End state (not yet built):

```text
matrix-maintainer mcp import https://github.com/example/server
matrix-maintainer mcp tag <id>
matrix-maintainer mcp verify <id>
matrix-maintainer mcp repair <id> --use-gitpilot
matrix-maintainer mcp report <id>
matrix-maintainer mcp publish <id>
```

New modules required (use the names from the plan; add them to the
existing package, don’t create a parallel tree):

```text
matrix_codex/
  mcp/
    discovery.py          # crawl GitHub topics, awesome-MCP lists, MatrixHub catalog
    manifest.py           # generate / validate MCP manifest
    tagging.py            # capability/runtime/risk/quality/maintenance tags
    license.py            # SPDX detection + policy gate
    verify.py             # sandbox install + health check via SelfRepair
    repair.py             # SelfRepair-safe → GitPilot-complex escalation
  patches/
    generate.py           # `git diff` against upstream verified commit
    apply.py              # patch + sha256 verification
    metadata.py           # manifest + provenance record
    storage_adapter.py    # multi-backend writer
  storage/
    github_patches.py     # primary mirror: agent-matrix/mcp-patches
    huggingface_patches.py# archival mirror: HF dataset
    cloudflare_r2.py      # CDN tier for install-time delivery
  matrixhub/
    manifest_update.py    # write verified manifests back to MatrixHub
    status_badges.py      # publish badge metadata
```

### 6.3 Surface C — patch-on-install client (deferred)

`matrix install <mcp-server>` belongs in `agent-matrix/matrix-cli`,
**not** here. Matrix-Maintainer is the producer of patches and
manifests; matrix-cli is the consumer. This document doesn’t design
the client; it only commits to a stable storage contract the client
can rely on.

---

## 7. Industry best-practice patterns to apply

These are the patterns that should shape the next phase of work. None
of them are exotic — they are the table stakes for a control-plane
that touches many repositories.

1. **Control-plane / data-plane split (already adopted).** The
   controller dispatches workflows; the worker does the work in the
   target repo’s own context. Preserve this. Resist the pull to
   centralize repo checkouts.

2. **Idempotent jobs keyed by (repo, issue\_type, content\_hash).**
   Today `RunRecord` carries a `run_id` but no dedup key. Add a
   content hash on the planned task so retries don’t open duplicate
   PRs.

3. **Event sourcing for the audit log.** `StorageDB` already appends
   `EventRecord`s — formalize the schema (jsonschema), version it,
   and treat the JSON file as the source of truth for replay. Project
   secondary views (status site, badges) from the event stream.

4. **Two-phase apply for repairs.** Plan → Approve → Apply → Validate
   → Publish. Never collapse plan and apply into one step. The
   existing `scan → plan → run → report` already encodes this; keep
   the phases addressable from the CLI so an operator can stop after
   "plan".

5. **Risk-tiered approval gates** (already in `config/policies.yml`).
   Make the gate explicit in the PR body so reviewers see *why* a
   task is auto-mergeable vs. requires human review.

6. **Signed and hashed patches.** Every patch artifact carries:
   `sha256`, `upstream_repo`, `upstream_commit`, `patch_format`
   (`git-format-patch`/`unified`), `tool_version`, optional
   Sigstore signature. The MatrixHub manifest references this record
   by digest, not URL — URLs rot, digests don’t.

7. **Pluggable storage backends behind one interface.** The plan lists
   GitHub + HF + R2. Define one writer interface, ship a GitHub
   implementation first, add HF and R2 as parallel backends behind
   the same call. Decide which backend is *authoritative* (proposal:
   GitHub) and which are mirrors.

8. **Default to draft PRs.** Never auto-merge. Already in
   `config/policies.yml` — keep it that way; add a CI check that
   blocks `auto-merge: true` in any PR opened by the controller for
   high-risk task types.

9. **Sandbox isolation that mirrors target runtime.** SelfRepair
   already uses MatrixLab for this. Matrix-Maintainer must not run
   `make install` directly on the controller host — always through
   the sandbox client.

10. **Observability minimums**: structured logs with `run_id`,
    `task_id`, `repo`, `phase`; Prometheus counters for
    `runs_total{status=…}`, `tasks_total{risk_level=…}`,
    `dispatch_failures_total`; a `/health` and `/ready` distinction
    in the FastAPI app.

11. **One source of truth for repo inventory.** Today: `.matrix/repo.yml`
    in each repo, `config/repos.yml` and `config/repositories.yml`
    centrally, plus GitHub org discovery. Pick one as the source and
    let the others derive from it. Recommendation: GitHub org
    discovery is the source; `.matrix/repo.yml` is the per-repo
    override; `config/repos.yml` is an explicit allow/deny list.

12. **Versioned manifests with SchemaVersion**. Already used in the
    `cli.py:check_make` report (`schema_version: "0.1"`). Apply the
    same pattern to MCP manifests, patch metadata, and event records.

---

## 8. Reference architecture (consolidated)

```text
                          MatrixHub Catalog (publish trust + metadata)
                                        ▲
                                        │ verified manifests, status badges
                                        │
   ┌──────────────┐        ┌─────────────────────────────┐        ┌────────────────────┐
   │ OllaBridge   │◄──────►│   Matrix-Maintainer         │───────►│  GitHub / GitLab   │
   │ LLM gateway  │        │   (this repo)               │        │  repos + PRs       │
   └──────────────┘        │                             │        └────────────────────┘
                           │  ┌────────────────────────┐ │
                           │  │ Inventory (org/MCP)    │ │
                           │  │ Pipeline (scan→…→report)│ │
                           │  │ Dispatcher (Actions)   │ │
                           │  │ Policy / Treasury      │ │
                           │  │ Storage / Event log    │ │
                           │  │ Patches (gen/apply)    │ │
                           │  └────────────────────────┘ │
                           └────────────┬────────────────┘
                                        │ thin clients
              ┌─────────────────────────┼─────────────────────────┐
              ▼                         ▼                         ▼
      ┌──────────────┐          ┌───────────────┐         ┌────────────────┐
      │  SelfRepair  │          │   GitPilot    │         │ Patch storage  │
      │ scan/heal/   │          │ AI code edits │         │ GH + HF + R2   │
      │ validate     │          │ + tests loop  │         │ (sha256/sig)   │
      └──────────────┘          └───────────────┘         └────────────────┘
```

---

## 9. Roadmap (concrete, ordered)

Each item below is sized to be a single PR series of <≈400 LOC.

### Phase 0 — branding + boundary cleanup (1–2 days)

- P0.1  Add `matrix-maintainer` console-script alias to
        `pyproject.toml`; keep `matrix-codex` working.
- P0.2  Rewrite README so "Matrix Maintainer" is the product name and
        Codex is the engine codename. One pass, one consistent voice.
- P0.3  Merge `apps/backend/` into `app/` and delete the duplicate
        FastAPI surface.
- P0.4  Decide a single repo-inventory source of truth (per §7).

### Phase 1 — SelfRepair adapter (the unblock for everything else)

- P1.1  Define `selfrepair/client.py` (Protocol + Pydantic DTOs).
- P1.2  Implement `SelfRepairLocalClient` first (no network).
- P1.3  Replace `matrix_codex/healing/`, `analyzers/`,
        `health_scanner.py` callers with the client.
- P1.4  Mark old internal modules deprecated; tests must pass against
        the client.
- P1.5  Add `SelfRepairHttpClient` against SelfRepair `/v1/rpc`.

### Phase 2 — friendlier CLI for Surface A

- P2.1  `matrix-maintainer scan-org <org> [--report-only]`
- P2.2  `matrix-maintainer repair-repo <full_name> [--safe-only] [--open-draft-pr]`
- P2.3  `matrix-maintainer repair-org <org> [--use-gitpilot] [--open-draft-pr]`
- P2.4  PR body template that embeds SelfRepair JSON + HTML reports.

### Phase 3 — MCP verification (Surface B, MVP-2)

- P3.1  `mcp import <url>` → manifest skeleton + license scan.
- P3.2  `mcp tag <id>` → capability/runtime/risk/quality tags.
- P3.3  `mcp verify <id>` → sandbox install + health check via
        SelfRepair client.
- P3.4  `mcp report <id>` → write report into `state/mcp/<id>.json`.
- P3.5  `mcp publish <id>` → push verified manifest to MatrixHub.

### Phase 4 — Patch archive (MVP-3 producer side)

- P4.1  `patches/generate.py` from sandbox-applied fixes.
- P4.2  `storage/github_patches.py` writes to
        `agent-matrix/mcp-patches`.
- P4.3  Patch metadata record schema (signed manifest with sha256).
- P4.4  `huggingface_patches.py` mirror; `cloudflare_r2.py` mirror.
- P4.5  Document the consumer contract for `matrix-cli` to implement.

### Phase 5 — Hardening

- P5.1  Prometheus exporters and `/ready` endpoint.
- P5.2  Schema versioning + jsonschema validation across event records.
- P5.3  Sigstore signing of commits and patches behind a feature flag.
- P5.4  Replace JSON `StorageDB` with SQLite (still file-backed) for
        concurrent worker writes.

---

## 10. Open questions for the maintainers

These are decisions only humans should make; they shape later phases.

1. **PyPI rename**: are we willing to publish as `matrix-maintainer`
   while keeping the `matrix_codex` import name, or do we want a hard
   rename of the import path too?
2. **SelfRepair coupling**: do we vendor SelfRepair as a Python
   dependency, run it as a co-located service, or both?
3. **Authoritative patch backend**: GitHub repo (cheap, public,
   versioned) vs. HF dataset (size, public) vs. R2 (private, fast).
   Recommendation: GitHub authoritative, HF + R2 mirrors. Confirm.
4. **MatrixHub publish protocol**: REST POST today, or do we want an
   event-bus contract (e.g. via OllaBridge)?
5. **Org scope**: MVP-1 targets `agent-matrix` org only. Do we
   formally scope-lock that in `config/policies.yml` until Phase 3 is
   green?

---

*End of design. Implementation will land in follow-up PRs, one phase
at a time.*
