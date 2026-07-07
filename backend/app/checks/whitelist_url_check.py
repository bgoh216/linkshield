from fnmatch import fnmatch
from urllib.parse import urlparse

from ..interfaces import CheckResult

# Domain patterns; "*" matches any subdomain segment (e.g. "*.gov.sg" matches "www.gov.sg")
WHITELIST_DOMAINS = [
    "*.gov.sg",
    "*",
]

class WhitelistURLCheck:
    """
    Stub for a real whitelist check (e.g. against a database of known safe URLs)
    Swap this out or add a sibling (e.g. DatabaseWhitelistCheck) and register it
    """

    name = "whitelist"

    async def check(self, url: str) -> CheckResult:
        hostname = urlparse(url).hostname or ""
        is_whitelisted = any(fnmatch(hostname, pattern) for pattern in WHITELIST_DOMAINS)
        if is_whitelisted:
            return CheckResult(True, self.name)
        return CheckResult(False, self.name, f"'{hostname or url}' is not on the allowed domain list")
