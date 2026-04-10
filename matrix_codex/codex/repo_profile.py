from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RepoProfile:
    full_name: str
    default_branch: str = "main"
    language_hint: str | None = None
