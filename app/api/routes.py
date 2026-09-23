from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.control.dispatcher import DispatchRequest, Dispatcher
from app.control.improvement import EvalResult, ImprovementPolicy, ImprovementProposal, evaluate_improvement
from app.db.database import get_session
from app.db.models import Event, Run

router = APIRouter()


class EventInput(BaseModel):
    run_id: str = Field(min_length=1)
    repo: str = Field(min_length=1)
    status: str = Field(min_length=1)
    pr_url: str | None = None


class DispatchInput(BaseModel):
    repo: str = Field(min_length=1)
    issue: str = Field(min_length=1)


@router.post("/event")
def receive_event(event: EventInput, session: Session = Depends(get_session)) -> dict[str, str]:
    run = session.get(Run, event.run_id)
    if run is None:
        run = Run(id=event.run_id, repo=event.repo, status=event.status, operation="external-event")
        session.add(run)
    else:
        run.status = event.status

    session.add(
        Event(
            run_id=event.run_id,
            payload={
                "repo": event.repo,
                "status": event.status,
                "pr_url": event.pr_url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    )
    session.commit()
    return {"status": "received"}


@router.get("/runs")
def list_runs(session: Session = Depends(get_session)) -> list[dict[str, str]]:
    rows = session.query(Run).order_by(Run.created_at.desc()).limit(100).all()
    return [
        {
            "id": row.id,
            "repo": row.repo,
            "status": row.status,
            "operation": row.operation,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.post("/dispatch")
def dispatch(input_data: DispatchInput, session: Session = Depends(get_session)) -> dict[str, str]:
    request = DispatchRequest(repo=input_data.repo, issue=input_data.issue)
    run_id = Dispatcher(session=session).dispatch(request)
    return {"status": "triggered", "run_id": run_id}


class ImprovementInput(BaseModel):
    repo: str = Field(min_length=1)
    hypothesis: str = Field(min_length=3)
    target_files: list[str] = Field(default_factory=list)
    baseline_score: float
    candidate_score: float
    safety_regressions: int = 0
    reproducible: bool = True
    estimated_cost_mxu: float = 0.0
    budget_remaining_mxu: float = 0.0
    capability_changing: bool = False


@router.post("/improvements/evaluate")
def evaluate_candidate(input_data: ImprovementInput) -> dict:
    proposal = ImprovementProposal(
        repo=input_data.repo,
        hypothesis=input_data.hypothesis,
        target_files=tuple(input_data.target_files),
        capability_changing=input_data.capability_changing,
    )
    result = EvalResult(
        baseline_score=input_data.baseline_score,
        candidate_score=input_data.candidate_score,
        safety_regressions=input_data.safety_regressions,
        reproducible=input_data.reproducible,
    )
    decision = evaluate_improvement(
        proposal,
        result,
        ImprovementPolicy(),
        estimated_cost_mxu=input_data.estimated_cost_mxu,
        budget_remaining_mxu=input_data.budget_remaining_mxu,
    )
    return decision.to_dict()
