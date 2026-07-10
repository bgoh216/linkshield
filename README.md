# LinkShield

Link shortener with pluggable URL safety checks and click tracking.

Stack: Next.js (TypeScript) frontend, FastAPI backend, PostgreSQL.

## Setup

### Prerequisites
- Docker + Docker Compose (Option A), or Python 3.11+ and Node 20+ (Option B)

### Option A: Docker Compose (everything, one command)
```bash
docker compose up -d --build
```
All required env vars (DB credentials, `ACTIVE_SECURITY_CHECKS`,
`NEXT_PUBLIC_API_BASE`, etc.) are already set in `docker-compose.yml`, so
no `.env` files are needed — just run the command above.

Frontend at http://localhost:3000, backend/docs at http://localhost:8000/docs.
Postgres data persists in the `pgdata` volume. Rebuild after dependency
changes with `docker compose up -d --build`; tear down with
`docker compose down` (add `-v` to also wipe the database volume).

### Option B: run each piece natively

Unlike Option A, running natively means each service reads its config from
its own `.env` file, so you'll need to copy the provided examples first.

**1. Start Postgres**
```bash
docker compose up -d db
```

**2. Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit if needed
uvicorn app.main:app --reload --port 8000
```
API docs at http://localhost:8000/docs

Backend env vars (`backend/.env`, copied from `backend/.env.example`):
```
DATABASE_URL=postgresql://linkshield:linkshield@localhost:5432/linkshield
FRONTEND_CORS_ORIGINS=http://localhost:3000
ACTIVE_SECURITY_CHECKS=ssrf,reputation,whitelist,blacklist
ACTIVE_TRACKERS=db
```
`ACTIVE_SECURITY_CHECKS` / `ACTIVE_TRACKERS` are optional — see `config.py`
for defaults if unset.

**3. Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
App at http://localhost:3000

Frontend env vars (`frontend/.env.local`, copied from
`frontend/.env.local.example`):
```
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_APP_BASE=http://localhost:3000
```
These are inlined into the client bundle at build time, so in Docker
they're passed as build args rather than runtime env (see
`frontend/Dockerfile`).

**4. Backend tests**
```bash
cd backend
pytest
```

## Endpoints
- `POST /api/links` — create a short link `{ long_url, custom_code? }`
- `GET /api/links` — list all links with click counts
- `GET /api/links/{short_code}/stats` — click stats for one link
- `GET /r/{short_code}` — direct redirect (runs safety re-check before forwarding)
- `POST /api/links/{code}/click` — records a click with enrichment metadata, returns `{ redirect_url }`

## Security checks currently in place
- Scheme allowlist (only http/https)
- SSRF guard: resolves hostname and blocks private/loopback/link-local IP ranges
- Domain whitelist (`checks/whitelist_url_check.py`) and blacklist (`checks/blacklist_url_check.py`), `fnmatch`-based, both on by default
- Flag system: `is_flagged` links are blocked at redirect time
- Re-validation on every click, not just at creation time
- `ReputationCheck` (`checks/reputation_check.py`) is a stub — no external API wired in

## Possible extensions
- Real reputation API call in `ReputationCheck.check()`
- Database-backed whitelist/blacklist instead of hardcoded lists
- Rate limiting per IP/link on `/r/{short_code}`
- Admin view to review/unflag reported links
- Link expiry (`expires_at` column)
- QR code generation per link
- Auth-gated link creation

## Structure
```
linkshield/
  backend/         FastAPI app
    app/
      main.py             endpoints: create link, list links, stats, redirect
      models.py           SQLAlchemy models (Link, Click)
      schemas.py          Pydantic request/response models
      database.py         DB session setup
      interfaces.py       Protocol contracts: SecurityCheck, TrackingSink
      dependencies.py     FastAPI Depends() providers
      config.py           registry of available checks/trackers + which are active
      bot_detection.py    regex-based user-agent bot check
      checks/
        ssrf_check.py         blocks private/internal IPs (cloud metadata, localhost, LAN)
        reputation_check.py   stub for Safe Browsing / VirusTotal
        whitelist_url_check.py  denies any domain not on an allowlist (e.g. *.gov.sg)
        blacklist_url_check.py  blocks known-bad domains (e.g. *.badsite.com)
        pipeline.py            runs a list of checks against a URL
      tracking/
        db_tracker.py        writes clicks to Postgres (always on)
        external_tracker.py  stub for plugging in a third-party analytics API
    tests/                pytest suite (checks, schemas, bot detection, /api/links)
    requirements.txt
    Dockerfile
  frontend/        Next.js app (App Router, TS, Tailwind)
    app/page.tsx           form to create links + list view
    app/go/[code]/         interstitial redirect page (see below)
    lib/api.ts              fetch helpers for backend
    lib/botDetection.ts      frontend copy of the bot-pattern check
    Dockerfile
  docker-compose.yml   Postgres + backend + frontend
```

## Database
![erd](image.png)

Two tables, one-to-many (`links` 1 — * `clicks`):

- **links** — `id`, `short_code` (unique, indexed), `long_url`, `created_at`, `is_flagged`, `is_verified_safe`, `last_checked_at`.
- **clicks** — `id`, `link_id` (FK), `clicked_at`, `ip_address`, `user_agent`, `referrer`, `device_metadata` (JSON — screen size, timezone, language, etc.).

`device_metadata` is JSON rather than fixed columns because the set of
enrichment fields collected on click is expected to change; adding a field
doesn't require a migration.

## Architecture

Routes don't instantiate `SSRFCheck()` or `DBClickTracker()` directly — they
get them through FastAPI's `Depends()`:

```python
async def create_link(payload: ..., pipeline: SecurityPipeline = Depends(get_security_pipeline)):
    result = await pipeline.run(long_url)
```

`get_security_pipeline()` (`dependencies.py`) builds the pipeline from
whatever is listed in `config.py`'s `ACTIVE_CHECKS`, driven by an env var
(`ACTIVE_SECURITY_CHECKS=ssrf,reputation,whitelist,blacklist`). Adding a
check means writing a class with an async `check(url) -> CheckResult`
method, registering it in `SECURITY_CHECK_REGISTRY`, and adding its name to
the env var — no changes to `main.py` or other checks. Trackers follow the
same pattern via `TRACKER_FACTORIES` / `ACTIVE_TRACKERS`.

`TrackingSink.record_click()` takes a generic `metadata: dict | None`
instead of one named parameter per field, so adding a tracked field doesn't
require touching every `TrackingSink` implementation.

### Redirect flow

A short link doesn't 302 straight to its target. It goes through a Next.js
page first so the client can collect data (screen size, timezone,
language) that a server-side redirect never gets access to, then POSTs it
to the backend before the final redirect:

```
GET /go/{code}                 (Next.js page)
  bot user-agent?  → redirect() straight to /r/{code}   (no JS involved)
  else             → render interstitial
                       → JS collects screen/timezone/language
                       → POST /api/links/{code}/click  (metadata)
                       → backend re-runs SecurityPipeline, records click
                       → backend returns { redirect_url }
                       → window.location.replace(redirect_url)
```

The bot branch exists because link-preview bots (WhatsApp, Slack, iMessage),
crawlers, and CLI tools don't execute JavaScript — without it they'd hit a
blank interstitial and never reach the destination. `/go/{code}` is a
server component that checks `User-Agent` against known bot patterns
(`bot_detection.py` on the backend, `lib/botDetection.ts` on the frontend —
same list, kept in sync manually) before rendering anything.

`GET /r/{code}` is unchanged from before this existed; it's the direct
redirect path, used as the bot fallback and reachable directly.

Trade-off: real users get an extra hop and a short visible delay (typically
under 300ms) before landing on the destination, in exchange for the
enrichment data.
</content>
