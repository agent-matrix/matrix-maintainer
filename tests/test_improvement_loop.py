from app.control.improvement import (
    EvalResult,
    ImprovementPolicy,
    ImprovementProposal,
    assert_pr_only,
    evaluate_improvement,
)


def proposal(capability=False):
    return ImprovementProposal("agent-matrix/matrix-os", "improve routing", ("matrix_os/router.py",), capability)


def test_good_candidate_can_only_become_pr():
    d = evaluate_improvement(
        proposal(),
        EvalResult(.70, .76, 0, True),
        ImprovementPolicy(),
        estimated_cost_mxu=10,
        budget_remaining_mxu=100,
    )
    assert d.approved_for_pr and d.action == "create_pull_request"
    assert_pr_only(d)


def test_safety_regression_blocks_candidate():
    d = evaluate_improvement(
        proposal(),
        EvalResult(.70, .90, 1, True),
        ImprovementPolicy(),
        estimated_cost_mxu=10,
        budget_remaining_mxu=100,
    )
    assert not d.approved_for_pr


def test_capability_change_requires_human():
    d = evaluate_improvement(
        proposal(True),
        EvalResult(.70, .76, 0, True),
        ImprovementPolicy(),
        estimated_cost_mxu=10,
        budget_remaining_mxu=100,
    )
    assert d.requires_human_approval
