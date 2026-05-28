"""SPDX-aware license classification and policy gating.

We intentionally keep this small. For full SPDX resolution use a
library; for the orchestrator-side gating we just need a fast
classifier into one of five buckets so policy decisions become
deterministic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

PolicyClass = Literal[
    "permissive",
    "weak-copyleft",
    "strong-copyleft",
    "restricted",
    "unknown",
]

# Identifier -> bucket. Lower-cased keys; values are policy classes.
_LICENSE_TABLE: dict[str, PolicyClass] = {
    "mit": "permissive",
    "apache-2.0": "permissive",
    "apache 2.0": "permissive",
    "bsd-2-clause": "permissive",
    "bsd-3-clause": "permissive",
    "isc": "permissive",
    "0bsd": "permissive",
    "unlicense": "permissive",
    "mpl-2.0": "weak-copyleft",
    "lgpl-2.1": "weak-copyleft",
    "lgpl-3.0": "weak-copyleft",
    "eupl-1.2": "weak-copyleft",
    "gpl-2.0": "strong-copyleft",
    "gpl-3.0": "strong-copyleft",
    "agpl-3.0": "strong-copyleft",
    "sspl-1.0": "restricted",
    "bsl-1.1": "restricted",
    "elastic-2.0": "restricted",
    "cc-by-nc-4.0": "restricted",
    "proprietary": "restricted",
}

_DEFAULT_ALLOWED: tuple[PolicyClass, ...] = ("permissive", "weak-copyleft")


@dataclass(slots=True, frozen=True)
class LicenseDecision:
    spdx_id: str | None
    policy_class: PolicyClass
    allowed: bool
    reason: str


def classify(spdx_id: str | None) -> PolicyClass:
    if not spdx_id:
        return "unknown"
    key = spdx_id.strip().lower()
    return _LICENSE_TABLE.get(key, "unknown")


def detect_from_text(text: str) -> str | None:
    """Heuristic detection from a license file body."""

    if not text:
        return None
    head = text[:4000].lower()
    if "apache license" in head and "version 2.0" in head:
        return "Apache-2.0"
    if re.search(r"\bmit license\b", head):
        return "MIT"
    if "gnu affero general public license" in head:
        return "AGPL-3.0"
    if "gnu general public license" in head and "version 3" in head:
        return "GPL-3.0"
    if "gnu lesser general public license" in head:
        return "LGPL-3.0"
    if "mozilla public license" in head and "version 2.0" in head:
        return "MPL-2.0"
    if "business source license" in head:
        return "BSL-1.1"
    if "server side public license" in head:
        return "SSPL-1.0"
    if "bsd 3-clause" in head or "bsd-3-clause" in head:
        return "BSD-3-Clause"
    return None


def decide(
    spdx_id: str | None,
    *,
    allowed_classes: tuple[PolicyClass, ...] = _DEFAULT_ALLOWED,
) -> LicenseDecision:
    cls = classify(spdx_id)
    allowed = cls in allowed_classes
    if allowed:
        reason = f"{cls} license is on the allowlist"
    elif cls == "unknown":
        reason = "license could not be classified; require human review"
    else:
        reason = f"{cls} license is not on the allowlist {list(allowed_classes)}"
    return LicenseDecision(spdx_id=spdx_id, policy_class=cls, allowed=allowed, reason=reason)
