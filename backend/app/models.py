from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(16), unique=True, index=True, nullable=False)
    long_url = Column(String(2048), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Security / trust fields
    is_flagged = Column(Boolean, default=False)       # manually or auto flagged unsafe
    is_verified_safe = Column(Boolean, default=False) # passed reputation check
    last_checked_at = Column(DateTime(timezone=True), nullable=True)

    clicks = relationship("Click", back_populates="link", cascade="all, delete-orphan")


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    referrer = Column(String(2048), nullable=True)

    # Client-side enrichment data (screen size, timezone, language, viewport...).
    # Stored as a generic JSON blob rather than named columns — see README for why:
    # the shape of "what we enrich with" is expected to grow over time.
    device_metadata = Column(JSON, nullable=True)

    link = relationship("Link", back_populates="clicks")
