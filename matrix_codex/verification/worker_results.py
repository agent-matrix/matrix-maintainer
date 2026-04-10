from __future__ import annotations


def normalize_worker_conclusion(conclusion: str | None) -> str:
    mapping = {
        "success": "healthy",
        "neutral": "unknown",
        "failure": "down",
        "cancelled": "degraded",
        None: "unknown",
    }
    return mapping.get(conclusion, "unknown")
