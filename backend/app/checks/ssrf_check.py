import ipaddress
import socket
from urllib.parse import urlparse

from ..interfaces import CheckResult

ALLOWED_SCHEMES = {"http", "https"}

BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / cloud metadata
    ipaddress.ip_network("::1/128"),
]


class SSRFCheck:
    """Blocks URLs with disallowed schemes or that resolve to private/internal IPs."""

    name = "ssrf"

    async def check(self, url: str) -> CheckResult:
        parsed = urlparse(url)

        if parsed.scheme not in ALLOWED_SCHEMES:
            return CheckResult(False, self.name, f"Scheme '{parsed.scheme}' not allowed")

        if not parsed.hostname:
            return CheckResult(False, self.name, "URL has no hostname")

        try:
            resolved = socket.getaddrinfo(parsed.hostname, None)
        except socket.gaierror:
            return CheckResult(False, self.name, f"Could not resolve host: {parsed.hostname}")

        for _, _, _, _, sockaddr in resolved:
            ip = ipaddress.ip_address(sockaddr[0])
            for network in BLOCKED_NETWORKS:
                if ip in network:
                    return CheckResult(False, self.name, "URL resolves to a private/internal address")

        return CheckResult(True, self.name)
