// Mirrors backend/app/bot_detection.py — kept in sync manually since this is
// a small, stable list. If you add a pattern on one side, add it on the other.
const BOT_PATTERN =
  /bot|crawl|spider|slurp|facebookexternalhit|whatsapp|slackbot|telegrambot|discordbot|curl|wget|python-requests|headless|preview/i;

export function isBot(userAgent: string | null): boolean {
  if (!userAgent) return true;
  return BOT_PATTERN.test(userAgent);
}
