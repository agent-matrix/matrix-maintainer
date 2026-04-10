from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Print rollout plan for worker template installation")
    parser.add_argument("--config", default="config/repositories.yml")
    args = parser.parse_args()

    data = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    org = data["organization"]
    repos = data["repositories"]

    print("Planned rollout targets:")
    for repo in repos:
        name = repo if isinstance(repo, str) else repo["name"]
        print(f"- {org}/{name}: add .github/workflows/matrix-codex-worker.yml and AGENTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
