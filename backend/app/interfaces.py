"""
Structural interfaces. Anything that matches these shapes can be used —
no inheritance required (Python's Protocol is duck-typing with type checking).

This is the contract that lets you swap SSRF checks, add a GDPR-compliant
tracker, add a Safe Browsing check, etc. without touching main.py.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class CheckResult:
    passed: bool
    check_name: str
    reason: str = ""


class SecurityCheck(Protocol):
    """One safety check to run against a URL (SSRF guard, reputation API, etc.)"""

    name: str

    async def check(self, url: str) -> CheckResult:
        ...


class TrackingSink(Protocol):
    """One place to record a click (DB, analytics API, audit log, etc.)"""

    name: str

    async def record_click(self, *, link_id: int, ip_address: str | None,
                            user_agent: str | None, referrer: str | None,
                            metadata: dict | None = None) -> None:
        ...
