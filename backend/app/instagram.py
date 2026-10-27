"""Phase 6: Instagram permalink tracking for user-provided screenshots.

We deliberately do NOT scrape Instagram, bypass authentication, fetch remote
URLs, or repurpose oEmbed metadata for media discovery. Saved links provide
attribution to images users upload themselves.
"""
import re
from datetime import datetime
from urllib.parse import urlsplit
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

SHORTCODE = re.compile(r"^[A-Za-z0-9_-]{5,40}$")
ALLOWED_HOSTS = {"instagram.com", "www.instagram.com", "m.instagram.com"}
KINDS = {"p": "post", "reel": "reel", "tv": "video"}


def normalize_instagram_url(value: str) -> tuple[str, str, str]:
    """Fixed allowlist + strict paths; safe to store, never used for server fetches."""
    if len(value) > 2048:
        raise ValueError("Link zu lang")
    parsed = urlsplit(value.strip())
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in ALLOWED_HOSTS:
        raise ValueError("Nur HTTPS-Links zu instagram.com werden unterstützt")
    if parsed.username or parsed.password or parsed.port is not None:
        raise ValueError("Link enthält nicht unterstützte Bestandteile")
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 2 or parts[0] not in KINDS or not SHORTCODE.fullmatch(parts[1]):
        raise ValueError("Bitte einen Instagram-Beitrags- oder Reel-Link einfügen")
    return f"https://www.instagram.com/{parts[0]}/{parts[1]}/", parts[1], KINDS[parts[0]]


class NewImport(BaseModel):
    url: str = Field(min_length=12, max_length=2048)


class LinkItem(BaseModel):
    media_id: int = Field(ge=1)


def build_instagram_router(Base, MediaItem, engine):
    class InstagramSource(Base):
        __tablename__ = "instagram_sources"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        url: Mapped[str] = mapped_column(String(240), unique=True, nullable=False)
        shortcode: Mapped[str] = mapped_column(String(40), nullable=False)
        kind: Mapped[str] = mapped_column(String(12), nullable=False)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    class SourceMedia(Base):
        __tablename__ = "instagram_source_media"
        __table_args__ = (UniqueConstraint("source_id", "media_id", name="uq_instagram_source_media"),)
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        source_id: Mapped[int] = mapped_column(ForeignKey("instagram_sources.id", ondelete="CASCADE"), nullable=False)
        media_id: Mapped[int] = mapped_column(ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)

    router = APIRouter(prefix="/api/instagram", tags=["instagram"])

    def serialize(session, entry):
        associations = session.scalars(select(SourceMedia).where(SourceMedia.source_id == entry.id)).all()
        return {
            "id": entry.id, "url": entry.url, "shortcode": entry.shortcode, "kind": entry.kind,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "media_ids": [rel.media_id for rel in associations],
            "import_mode": "manual_screenshots",
        }

    @router.get("/sources")
    def list_sources():
        with Session(engine) as session:
            entries = session.scalars(select(InstagramSource).order_by(InstagramSource.id.desc()).limit(200)).all()
            return [serialize(session, entry) for entry in entries]

    @router.post("/sources", status_code=201)
    def add_source(payload: NewImport):
        try:
            normalized, shortcode, kind = normalize_instagram_url(payload.url)
        except (ValueError, OverflowError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        with Session(engine) as session:
            existing = session.scalar(select(InstagramSource).where(InstagramSource.url == normalized))
            if existing:
                return serialize(session, existing) | {"existing": True}
            record = InstagramSource(url=normalized, shortcode=shortcode, kind=kind)
            session.add(record)
            session.commit()
            session.refresh(record)
            return serialize(session, record) | {"existing": False}

    @router.post("/sources/{source_id}/media")
    def associate(source_id: int, payload: LinkItem):
        with Session(engine) as session:
            entry = session.get(InstagramSource, source_id)
            media = session.get(MediaItem, payload.media_id)
            if not entry or not media:
                raise HTTPException(status_code=404, detail="Quelle oder Medium nicht gefunden")
            existing = session.scalar(select(SourceMedia).where(
                SourceMedia.source_id == source_id, SourceMedia.media_id == payload.media_id))
            if not existing:
                session.add(SourceMedia(source_id=source_id, media_id=payload.media_id))
                session.commit()
            return serialize(session, entry)

    @router.delete("/sources/{source_id}", status_code=204)
    def delete_source(source_id: int):
        with Session(engine) as session:
            record = session.get(InstagramSource, source_id)
            if not record:
                raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
            for link in session.scalars(select(SourceMedia).where(SourceMedia.source_id == source_id)).all():
                session.delete(link)
            session.delete(record)
            session.commit()

    return router, SourceMedia
