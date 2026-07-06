import re

# Known link-preview bots (WhatsApp, Slack, iMessage, etc.), crawlers, and CLI
# tools. These don't run JavaScript, so they must never be served the
# interstitial page — they need a plain, immediate redirect.
BOT_PATTERNS = re.compile(
    r"bot|crawl|spider|slurp|facebookexternalhit|whatsapp|slackbot|"
    r"telegrambot|discordbot|curl|wget|python-requests|headless|preview",
    re.IGNORECASE,
)


def is_bot(user_agent: str | None) -> bool:
    if not user_agent:
        # No UA at all is unusual for a real browser — treat cautiously as a bot
        # so we never rely on JS running for something that isn't a browser.
        return True
    return bool(BOT_PATTERNS.search(user_agent))
