"""
FastAPI dependency providers. Routes ask for `SecurityPipeline` or
`list[TrackingSink]` via Depends() and get whatever's configured in
config.py — routes never know or care which concrete classes are active.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from .checks import SecurityPipeline
from .config import SECURITY_CHECK_REGISTRY, ACTIVE_CHECKS, TRACKER_FACTORIES, ACTIVE_TRACKERS
from .database import get_db
from .interfaces import TrackingSink


def get_security_pipeline() -> SecurityPipeline:
    checks = [SECURITY_CHECK_REGISTRY[name]() for name in ACTIVE_CHECKS if name in SECURITY_CHECK_REGISTRY]
    return SecurityPipeline(checks)


def get_trackers(db: Session = Depends(get_db)) -> list[TrackingSink]:
    return [TRACKER_FACTORIES[name](db) for name in ACTIVE_TRACKERS if name in TRACKER_FACTORIES]
