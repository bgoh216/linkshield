"""
Example of a second, optional tracker — shows the plug-and-play pattern.
Wire this up to PostHog/Segment/whatever and add "external" to ACTIVE_TRACKERS
in config.py to turn it on. No changes needed in main.py or db_tracker.py.
"""


class ExternalAnalyticsTracker:
    name = "external"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    async def record_click(self, *, link_id: int, ip_address: str | None,
                            user_agent: str | None, referrer: str | None,
                            metadata: dict | None = None) -> None:
        # TODO: fire an async HTTP call to your analytics provider here.
        # Kept as a no-op stub so it's safe to enable before it's implemented.
        pass
