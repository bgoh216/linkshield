from datetime import datetime
from pydantic import BaseModel, HttpUrl, ConfigDict, field_validator


class LinkCreateRequest(BaseModel):
    long_url: HttpUrl
    custom_code: str | None = None  # optional custom alias

    @field_validator("long_url", mode="before")
    @classmethod
    def reject_blank_url(cls, v):
        if isinstance(v, str) and not v.strip():
            raise ValueError("long_url must not be empty")
        return v


class LinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    long_url: str
    created_at: datetime
    is_flagged: bool
    is_verified_safe: bool
    click_count: int = 0


class LinkStatsResponse(BaseModel):
    short_code: str
    long_url: str
    total_clicks: int
    created_at: datetime
    

class ClickMetadata(BaseModel):
    """Client-side enrichment data collected by the frontend interstitial page."""
    screen_width: int | None = None
    screen_height: int | None = None
    viewport_width: int | None = None
    viewport_height: int | None = None
    timezone: str | None = None
    language: str | None = None


class ClickRedirectResponse(BaseModel):
    redirect_url: str
