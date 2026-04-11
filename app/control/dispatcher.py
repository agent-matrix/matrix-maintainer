from dataclasses import dataclass
import uuid

from sqlalchemy.orm import Session

from app.control.planner import build_plan
from app.db.models import Run
from app.integration.github_client import GitHubClient


@dataclass(slots=True)
class DispatchRequest:
    repo: str
    issue: str


class Dispatcher:
    def __init__(self, session: Session, github_client: GitHubClient | None = None) -> None:
        self.session = session
        self.github_client = github_client or GitHubClient()

    def dispatch(self, request: DispatchRequest) -> str:
        run_id = str(uuid.uuid4())
        plan = build_plan(request.repo, request.issue)
        self.session.add(Run(id=run_id, repo=request.repo, status="planned", operation=request.issue))
        self.session.commit()

        self.github_client.trigger_workflow(repo=request.repo, run_id=run_id, plan=plan)
        return run_id
