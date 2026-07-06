from ..interfaces import CheckResult


class ReputationCheck:
    """
    Stub for a real threat-intel API (Google Safe Browsing, VirusTotal, etc.)
    Swap this out or add a sibling (e.g. VirusTotalCheck) and register it —
    no changes needed elsewhere.
    """

    name = "reputation"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    async def check(self, url: str) -> CheckResult:
        # TODO: replace with a real async HTTP call, e.g.:
        # async with httpx.AsyncClient() as client:
        #     resp = await client.post(SAFE_BROWSING_URL, json={...})
        #     if resp.json().get("matches"):
        #         return CheckResult(False, self.name, "Flagged by Safe Browsing")
        return CheckResult(True, self.name)
