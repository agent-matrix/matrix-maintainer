import datetime as dt

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    default_branch = Column(String, default="main", nullable=False)
    config = Column(JSON, default=dict)


class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True)
    repo = Column(String, nullable=False)
    status = Column(String, nullable=False)
    operation = Column(String, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)


class WorkerExecution(Base):
    __tablename__ = "worker_executions"

    id = Column(Integer, primary_key=True)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    status = Column(String, nullable=False)
    logs = Column(String, default="")


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True)
    repo = Column(String, nullable=False)
    pr_url = Column(String, nullable=False)
    run_id = Column(String, nullable=False)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    run_id = Column(String, nullable=False)
    payload = Column(JSON, default=dict)
