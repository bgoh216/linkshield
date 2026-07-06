from ..interfaces import SecurityCheck, CheckResult


class SecurityPipeline:
    """Runs every configured check against a URL and reports the first failure (if any)."""

    def __init__(self, checks: list[SecurityCheck]):
        self.checks = checks

    async def run(self, url: str) -> CheckResult:
        for check in self.checks:
            result = await check.check(url)
            if not result.passed:
                return result
        return CheckResult(True, "pipeline")

    async def run_all(self, url: str) -> list[CheckResult]:
        """Run every check and return all results, even after a failure — useful for admin/debug views."""
        return [await check.check(url) for check in self.checks]
