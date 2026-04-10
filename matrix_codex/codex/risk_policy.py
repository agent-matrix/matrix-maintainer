from __future__ import annotations


SAFE_MODE_OPERATIONS = {"daily-maintenance", "lint-fix", "test-repair"}


def select_fix_mode(operation: str) -> str:
    return "safe" if operation in SAFE_MODE_OPERATIONS else "pr"
