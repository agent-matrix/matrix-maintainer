from __future__ import annotations


def build_operation_prompt(repo_full_name: str, operation: str) -> str:
    return (
        f"You are matrix-codex worker for {repo_full_name}. "
        f"Run operation '{operation}' safely, keep changes minimal, and run repo-local validation before opening a PR."
    )
