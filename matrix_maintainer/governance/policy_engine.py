from matrix_maintainer.governance.change_risk import classify_change_risk
from matrix_maintainer.governance.approval_rules import can_autofix

def evaluate_policy(changed_files: list[str]) -> dict:
    risk = classify_change_risk(changed_files)
    return {"risk": risk, "can_autofix": can_autofix(risk)}
