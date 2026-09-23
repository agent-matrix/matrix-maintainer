"""Governed recursive-improvement gate.

This module deliberately does not apply code. Its only successful terminal action
is to permit creation of a pull request containing a benchmarked candidate.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Tuple


@dataclass(frozen=True)
class ImprovementProposal:
    repo: str
    hypothesis: str
    target_files: Tuple[str, ...]
    capability_changing: bool = False


@dataclass(frozen=True)
class EvalResult:
    baseline_score: float
    candidate_score: float
    safety_regressions: int
    reproducible: bool

    @property
    def delta(self) -> float:
        return self.candidate_score - self.baseline_score


@dataclass(frozen=True)
class ImprovementPolicy:
    min_score_delta: float = 0.02
    max_safety_regressions: int = 0
    require_reproducible: bool = True
    require_human_for_capability_change: bool = True
    allowed_terminal_action: str = "create_pull_request"


@dataclass(frozen=True)
class PromotionDecision:
    approved_for_pr: bool
    requires_human_approval: bool
    action: str
    reasons: Tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_improvement(
    proposal: ImprovementProposal,
    result: EvalResult,
    policy: ImprovementPolicy,
    *,
    estimated_cost_mxu: float,
    budget_remaining_mxu: float,
) -> PromotionDecision:
    reasons = []

    if result.delta < policy.min_score_delta:
        reasons.append(f"benchmark delta {result.delta:.4f} below {policy.min_score_delta:.4f}")
    if result.safety_regressions > policy.max_safety_regressions:
        reasons.append("protected safety benchmark regressed")
    if policy.require_reproducible and not result.reproducible:
        reasons.append("candidate result is not reproducible")
    if estimated_cost_mxu > budget_remaining_mxu:
        reasons.append("candidate exceeds improvement budget")
    if not proposal.target_files:
        reasons.append("candidate has no bounded target files")

    approved = not reasons
    requires_human = approved and proposal.capability_changing and policy.require_human_for_capability_change

    return PromotionDecision(
        approved_for_pr=approved,
        requires_human_approval=requires_human,
        action=policy.allowed_terminal_action if approved else "reject_candidate",
        reasons=tuple(reasons) if reasons else ("benchmark and safety promotion gates passed",),
    )


def assert_pr_only(decision: PromotionDecision) -> None:
    if decision.approved_for_pr and decision.action != "create_pull_request":
        raise RuntimeError("recursive improvement may only terminate in a pull request")
