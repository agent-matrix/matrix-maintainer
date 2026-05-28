# SelfRepair Client Contract

> Status: stable as of `selfrepair/v1`
> Owner: agent-matrix/matrix-maintainer
> See also: `docs/design/matrix-maintainer-orchestration.md`

This document is the wire contract between Matrix-Maintainer and
SelfRepair. It is intentionally small. Anything not on this page is not
part of the contract and may change without notice.

## Contract surface

Four methods. Same signatures whether the client is local or HTTP:

| Method     | Inputs                                                | Output                |
| ---------- | ----------------------------------------------------- | --------------------- |
| `scan`     | `RepoRefDTO`, `profile?`                              | `RepoHealthReportDTO` |
| `repair`   | `RepoRefDTO`, `[HealthIssueDTO]`, `safe_only`, `branch?` | `RepairResultDTO`  |
| `validate` | `RepoRefDTO`, `in_sandbox`                            | `ValidationReportDTO` |
| `report`   | `RepoRefDTO`                                          | `JsonReportDTO`       |

All DTOs carry a `schema_version` string (currently `"selfrepair/v1"`).

## HTTP wire format

POST `{SELFREPAIR_BASE_URL}/v1/rpc` with a JSON-RPC 2.0 body:

```json
{
  "jsonrpc": "2.0",
  "id": "<uuid>",
  "method": "selfrepair.scan",
  "params": {"repo": {"full_name": "...", "clone_url": "..."}, "profile": "python"}
}
```

Responses follow JSON-RPC: either `result` (the DTO payload directly,
not wrapped) or `error: {code, message}`.

Authentication: `Authorization: Bearer <SELFREPAIR_API_KEY>` if the key
is set. SelfRepair MUST accept the missing-header case for local dev.

## Error semantics

Clients raise `SelfRepairError` on:

* HTTP 4xx (including 401/403)
* HTTP 5xx that survived the retry budget
* JSON-RPC `error` payload
* Unrecognized response shape

The orchestrator catches `SelfRepairError`, records the failure, and
continues with the next repo. A SelfRepair failure NEVER crashes the
control plane.

## Retry policy

* HTTP client: 3 attempts, exponential backoff 1s -> 8s, only on
  transport errors and 5xx.
* No retries on 4xx -- those are contract violations and must surface.

## Compatibility rules

1. New optional fields MAY be added to any DTO without bumping the
   schema version. Clients ignore unknown fields.
2. New required fields, removed fields, or changed semantics REQUIRE a
   new schema version (`selfrepair/v2`) and parallel support for one
   release window.
3. New methods MAY be added without a version bump as long as existing
   methods keep their signatures.
4. SelfRepair MUST advertise its supported schema versions at
   `GET /v1/about` (returns `{"schema_versions": ["selfrepair/v1"]}`).

## What lives on each side

Matrix-Maintainer (this repo):

* DTOs and Protocol -- `matrix_codex/selfrepair/`
* HTTP client + retry policy
* Local client (in-process bridge)
* The orchestrator that *uses* the client

SelfRepair:

* The actual scanning / healing / validation engines
* The `/v1/rpc` HTTP surface
* The `/v1/about` advertisement endpoint
* Optional: an importable `selfrepair.{scanners,healing,matrixlab}` API
  for the in-process LocalClient path. This is best-effort -- the
  LocalClient must still work without it (falling back to internal
  Matrix Codex modules during the migration window).
