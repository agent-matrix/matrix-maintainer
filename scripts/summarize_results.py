from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    path = Path("orchestration-results.json")
    if not path.exists():
        print("No orchestration-results.json found")
        return 1

    rows = json.loads(path.read_text(encoding="utf-8"))
    total = len(rows)
    ok = sum(1 for row in rows if row.get("ok"))
    failed = total - ok

    summary = {
        "total": total,
        "ok": ok,
        "failed": failed,
        "failed_repos": [row["repo"] for row in rows if not row.get("ok")],
    }
    out = Path("orchestration-summary.json")
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
