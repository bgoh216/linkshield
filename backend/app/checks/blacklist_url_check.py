from fnmatch import fnmatch
from urllib.parse import urlparse

from ..interfaces import CheckResult

# Domain patterns; "*" matches any subdomain segment (e.g. "*.badsite.com" matches "mirror.badsite.com")
BLACKLIST_DOMAINS = [
    "*.badsite.com",
    "*.yahoo.com"
]

class BlacklistURLCheck:
    """
    Stub for a real blacklist check (e.g. against a database of known malicious URLs)
    Swap this out or add a sibling (e.g. DatabaseBlacklistCheck) and register it
    """

    name = "blacklist"

    async def check(self, url: str) -> CheckResult:
        hostname = urlparse(url).hostname or ""
        is_blacklisted = any(fnmatch(hostname, pattern) for pattern in BLACKLIST_DOMAINS)
        if is_blacklisted:
            return CheckResult(False, self.name, f"'{hostname or url}' is on the blocked domain list")
        return CheckResult(True, self.name)
