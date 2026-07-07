import asyncio

from app.checks.whitelist_url_check import WhitelistURLCheck
from app.checks.blacklist_url_check import BlacklistURLCheck
from app.checks.pipeline import SecurityPipeline
from app.interfaces import CheckResult


def run(coro):
    return asyncio.run(coro)


def test_whitelist_allows_gov_sg_domain():
    result = run(WhitelistURLCheck().check("https://www.gov.sg/some/page"))
    assert result.passed is True


def test_whitelist_allows_arbitrary_domain_due_to_wildcard():
    # Known quirk: WHITELIST_DOMAINS includes a trailing "*" pattern, so
    # every hostname currently passes. This pins down that behavior.
    result = run(WhitelistURLCheck().check("https://totally-unrelated-domain.example/x"))
    assert result.passed is True


def test_blacklist_blocks_badsite_subdomain():
    result = run(BlacklistURLCheck().check("https://mirror.badsite.com/x"))
    assert result.passed is False
    assert result.check_name == "blacklist"


def test_blacklist_blocks_yahoo_subdomain():
    result = run(BlacklistURLCheck().check("https://mail.yahoo.com/x"))
    assert result.passed is False


def test_blacklist_allows_other_domains():
    result = run(BlacklistURLCheck().check("https://example.com/x"))
    assert result.passed is True


class FakeCheck:
    def __init__(self, name: str, passed: bool):
        self.name = name
        self._passed = passed

    async def check(self, url: str) -> CheckResult:
        return CheckResult(self._passed, self.name)


def test_pipeline_run_returns_first_failure():
    pipeline = SecurityPipeline([
        FakeCheck("first", True),
        FakeCheck("second", False),
        FakeCheck("third", True),
    ])
    result = run(pipeline.run("https://example.com"))
    assert result.passed is False
    assert result.check_name == "second"


def test_pipeline_run_passes_when_all_checks_pass():
    pipeline = SecurityPipeline([FakeCheck("first", True), FakeCheck("second", True)])
    result = run(pipeline.run("https://example.com"))
    assert result.passed is True
    assert result.check_name == "pipeline"


def test_pipeline_run_all_executes_every_check_regardless_of_failures():
    pipeline = SecurityPipeline([
        FakeCheck("first", True),
        FakeCheck("second", False),
        FakeCheck("third", True),
    ])
    results = run(pipeline.run_all("https://example.com"))
    assert len(results) == 3
    assert [r.check_name for r in results] == ["first", "second", "third"]
