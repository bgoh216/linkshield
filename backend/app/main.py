import random
import string

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import FRONTEND_CORS_ORIGINS

from . import models, schemas
from .database import engine, get_db, Base
from .checks import SecurityPipeline
from .dependencies import get_security_pipeline, get_trackers
from .interfaces import TrackingSink

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LinkShield API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_CORS_ORIGINS,  # frontend dev URL
    allow_methods=["*"],
    allow_headers=["*"],
)

CODE_ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int = 7) -> str:
    return "".join(random.choices(CODE_ALPHABET, k=length))

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/api/links", response_model=schemas.LinkResponse)
async def create_link(
    payload: schemas.LinkCreateRequest,
    db: Session = Depends(get_db),
    pipeline: SecurityPipeline = Depends(get_security_pipeline),
):
    long_url = str(payload.long_url)

    # Run every active security check (SSRF guard, reputation API, whatever
    # else gets registered later) via the injected pipeline.
    result = await pipeline.run(long_url)
    if not result.passed:
        raise HTTPException(status_code=400, detail=f"URL rejected ({result.check_name}): {result.reason}")

    is_safe = True

    # Resolve short code (custom alias or random, retry on collision)
    if payload.custom_code:
        code = payload.custom_code
        if db.query(models.Link).filter(models.Link.short_code == code).first():
            raise HTTPException(status_code=409, detail="Custom code already taken")
    else:
        code = generate_short_code()
        while db.query(models.Link).filter(models.Link.short_code == code).first():
            code = generate_short_code()

    link = models.Link(
        short_code=code,
        long_url=long_url,
        is_verified_safe=is_safe,
        is_flagged=not is_safe,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return schemas.LinkResponse(
        id=link.id,
        short_code=link.short_code,
        long_url=link.long_url,
        created_at=link.created_at,
        is_flagged=link.is_flagged,
        is_verified_safe=link.is_verified_safe,
        click_count=0,
    )


@app.get("/api/links", response_model=list[schemas.LinkResponse])
def list_links(db: Session = Depends(get_db)):
    links = db.query(models.Link).order_by(models.Link.created_at.desc()).all()
    results = []
    for link in links:
        results.append(
            schemas.LinkResponse(
                id=link.id,
                short_code=link.short_code,
                long_url=link.long_url,
                created_at=link.created_at,
                is_flagged=link.is_flagged,
                is_verified_safe=link.is_verified_safe,
                click_count=len(link.clicks),
            )
        )
    return results


@app.get("/api/links/{short_code}/stats", response_model=schemas.LinkStatsResponse)
def link_stats(short_code: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return schemas.LinkStatsResponse(
        short_code=link.short_code,
        long_url=link.long_url,
        total_clicks=len(link.clicks),
        created_at=link.created_at,
    )


@app.get("/r/{short_code}")
async def redirect_link(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
    pipeline: SecurityPipeline = Depends(get_security_pipeline),
    trackers: list[TrackingSink] = Depends(get_trackers),
):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.is_flagged:
        raise HTTPException(status_code=403, detail="This link has been flagged as unsafe")

    # Re-validate at click-time too — a link safe yesterday may not be today.
    result = await pipeline.run(link.long_url)
    if not result.passed:
        link.is_flagged = True
        db.commit()
        raise HTTPException(status_code=403, detail=f"This link failed a safety re-check ({result.check_name})")

    # Every active tracker gets a chance to record this click (DB always,
    # plus whatever else is turned on in config.py's ACTIVE_TRACKERS).
    # metadata={} here since this path serves bots/no-JS clients — no
    # client-side enrichment was possible.
    for tracker in trackers:
        await tracker.record_click(
            link_id=link.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer"),
            metadata={},
        )

    return RedirectResponse(url=link.long_url, status_code=302)


@app.post("/api/links/{short_code}/click", response_model=schemas.ClickRedirectResponse)
async def record_enriched_click(
    short_code: str,
    payload: schemas.ClickMetadata,
    request: Request,
    db: Session = Depends(get_db),
    pipeline: SecurityPipeline = Depends(get_security_pipeline),
    trackers: list[TrackingSink] = Depends(get_trackers),
):
    """
    Called by the frontend interstitial page (real browsers only — bots are
    routed to /r/{short_code} instead, see bot_detection.py). The frontend
    JS has already collected screen size, timezone, etc. and posts it here;
    we record the click with that metadata and hand back the real URL for
    the frontend to redirect to via window.location.
    """
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.is_flagged:
        raise HTTPException(status_code=403, detail="This link has been flagged as unsafe")

    result = await pipeline.run(link.long_url)
    if not result.passed:
        link.is_flagged = True
        db.commit()
        raise HTTPException(status_code=403, detail=f"This link failed a safety re-check ({result.check_name})")

    for tracker in trackers:
        await tracker.record_click(
            link_id=link.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer"),
            metadata=payload.model_dump(),
        )

    return schemas.ClickRedirectResponse(redirect_url=link.long_url)
