# Usage Guide

This is the quickest path to run Matrix Codex as a maintenance controller.

## 1) Install

```bash
make install
```

## 2) Validate local environment

```bash
matrix-codex --help
```

## 3) Run the maintenance loop manually

```bash
matrix-codex scan-health
matrix-codex plan-maintenance
matrix-codex run-maintenance
matrix-codex report-status
```

## 4) Run all tests

```bash
make test
```

If `uv` cannot download dependencies in your environment, run:

```bash
PYTHONPATH=. pytest -q
```

## 5) Publish status site

```bash
matrix-codex publish-site
```

## 6) Files you will edit most often

- `config/repositories.yml`
- `config/policies.yml`
- `config/tasks.yml`

## 7) Common troubleshooting

### Dispatch returns auth errors
- Verify `CROSS_REPO_TOKEN` or `GITHUB_TOKEN` exists and has Actions + PR permissions.

### No tasks generated
- Ensure scanner rules are active and repos in `config/repositories.yml` are valid.

### No status updates
- Verify workers are posting to `/event` and backend is running.
