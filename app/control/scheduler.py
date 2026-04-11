import uuid

from app.control.dispatcher import DispatchRequest, Dispatcher
from app.db.database import SessionLocal, init_db


def run() -> None:
    init_db()
    repos = ["agent-matrix/matrix-ai", "agent-matrix/matrix-guardian"]

    with SessionLocal() as session:
        dispatcher = Dispatcher(session=session)
        for repo in repos:
            dispatcher.dispatch(DispatchRequest(repo=repo, issue=f"daily-maintenance-{uuid.uuid4()}"))


if __name__ == "__main__":
    run()
