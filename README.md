# matrix-maintainer

`matrix-maintainer` is the daily health and standards agent for the Agent-Matrix organization.

It performs four core jobs:

1. discovers repositories in the target GitHub organization;
2. verifies build/runtime standards (`Makefile`, `pyproject.toml`, Python 3.11, `uv`, health tests);
3. attempts safe autofixes using GitPilot and verifies those fixes inside matrixlab-style sandboxes;
4. publishes a static status site to GitHub Pages.

## Core integrations

- **GitPilot** is used for repository analysis, action-plan generation, and GitHub-aware patch proposals.
- **matrixlab** is used for isolated execution of `make install`, `make test`, and `make start`.

## Production goals

- daily scheduled scans of all repositories
- low-risk automated PRs for missing standards
- static JSON + HTML status dashboard
- auditable logs and repeatable verification runs

## Quick start

```bash
cp .env.example .env
make install
make test
make start
```

## Daily operation

```bash
matrix-maintainer run-daily
matrix-maintainer publish-site
```

## GitHub Actions

The repository ships with:
- a daily scheduled maintainer workflow
- a site publishing workflow
- PR validation for this repository itself

## Environment variables

See `.env.example`.

## Repo standards enforced

- `Makefile` with `install`, `test`, `start`
- `pyproject.toml` with Python 3.11 and `uv`
- `tests/test_health.py`
- successful `make install`
- successful `make test`
- successful smoke-check of `make start`

## Notes

This repository is production-oriented, but its external integrations depend on:
- valid GitHub credentials
- a working GitPilot installation/CLI
- a working matrixlab installation/CLI or compatible sandbox adapter
- repository permissions to push branches and create PRs
