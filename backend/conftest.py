import os

# Must happen before any `app.*` import: app/main.py runs
# Base.metadata.create_all(bind=engine) at import time, and app/database.py
# builds that engine from DATABASE_URL (defaulting to a real Postgres URL).
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_security_pipeline
from app.interfaces import CheckResult

# Separate, explicit in-memory engine for actual test traffic. Plain
# create_engine("sqlite:///:memory:") defaults to SingletonThreadPool (one
# connection per thread), which is fragile under TestClient's worker-thread
# execution; StaticPool shares a single connection across threads instead.
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


class FakePassPipeline:
    async def run(self, url: str) -> CheckResult:
        return CheckResult(True, "fake")

    async def run_all(self, url: str) -> list[CheckResult]:
        return [CheckResult(True, "fake")]


class FakeRejectPipeline:
    def __init__(self, check_name: str = "fake", reason: str = "rejected by fake pipeline"):
        self.check_name = check_name
        self.reason = reason

    async def run(self, url: str) -> CheckResult:
        return CheckResult(False, self.check_name, self.reason)

    async def run_all(self, url: str) -> list[CheckResult]:
        return [CheckResult(False, self.check_name, self.reason)]


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_security_pipeline] = lambda: FakePassPipeline()
    with TestClient(app, follow_redirects=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()
