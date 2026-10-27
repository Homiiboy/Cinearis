"""Phase 4: collection editing and explicit per-episode progress."""
import json
import re
import unicodedata

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, create_engine, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column
from datetime import datetime


class MediaEdit(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    release_year: int | None = Field(default=None, ge=1870, le=2200)
    description: str | None = Field(default=None, max_length=1500)


class EpisodeChange(BaseModel):
    season: int = Field(ge=0, le=999)
    episode: int = Field(ge=1, le=99999)
    watched: bool


class SeasonChange(BaseModel):
    season: int = Field(ge=0, le=999)
    episode_count: int = Field(ge=1, le=2000)
    watched: bool


def canon(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    return re.sub(r"[^a-z0-9]+", "", "".join(c for c in value if not unicodedata.combining(c)))


def duplicate_for(session, MediaItem, *, title, kind, provider=None, provider_id=None, exclude_id=None):
    """Use exact provider identities and normalized names, never fuzzy automatic merging."""
    target = canon(title)
    for item in session.scalars(select(MediaItem).where(MediaItem.kind == kind)).all():
        if item.id == exclude_id:
            continue
        if provider and provider_id and item.provider == provider and item.provider_id == provider_id:
            return item
        names = [item.title, item.original_title or ""]
        try:
            names += json.loads(item.aliases_json or "[]")
        except (ValueError, TypeError):
            pass
        if target and target in {canon(n) for n in names if isinstance(n, str)}:
            return item
    return None


def build_collection_router(Base, MediaItem, engine, as_dict):
    class EpisodeProgress(Base):
        __tablename__ = "episode_progress"
        __table_args__ = (UniqueConstraint("media_id", "season", "episode", name="uq_episode_progress"),)
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        media_id: Mapped[int] = mapped_column(ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False, index=True)
        season: Mapped[int] = mapped_column(Integer, nullable=False)
        episode: Mapped[int] = mapped_column(Integer, nullable=False)
        watched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    router = APIRouter(tags=["collection"])

    @router.patch("/api/media/{item_id}")
    def edit_media(item_id: int, payload: MediaEdit):
        with Session(engine) as session:
            item = session.get(MediaItem, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Titel nicht gefunden")
            title = payload.title.strip()
            if not title:
                raise HTTPException(status_code=422, detail="Titel darf nicht leer sein")
            duplicate = duplicate_for(session, MediaItem, title=title, kind=item.kind, exclude_id=item_id)
            if duplicate:
                raise HTTPException(status_code=409, detail=f"Ein Titel mit diesem Namen existiert bereits (ID {duplicate.id}).")
            item.title = title
            item.release_year = payload.release_year
            item.description = payload.description
            session.commit()
            session.refresh(item)
            return as_dict(item)

    def require_series(session, item_id: int):
        item = session.get(MediaItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Titel nicht gefunden")
        if item.kind == "movie":
            raise HTTPException(status_code=422, detail="Filme besitzen keine Staffeln oder Episoden")
        return item

    @router.get("/api/media/{item_id}/episodes")
    def get_episodes(item_id: int):
        with Session(engine) as session:
            require_series(session, item_id)
            entries = session.scalars(select(EpisodeProgress).where(
                EpisodeProgress.media_id == item_id).order_by(EpisodeProgress.season, EpisodeProgress.episode)).all()
            return [{"season": e.season, "episode": e.episode} for e in entries]

    @router.put("/api/media/{item_id}/episodes")
    def set_episode(item_id: int, payload: EpisodeChange):
        with Session(engine) as session:
            require_series(session, item_id)
            existing = session.scalar(select(EpisodeProgress).where(
                EpisodeProgress.media_id == item_id, EpisodeProgress.season == payload.season,
                EpisodeProgress.episode == payload.episode))
            if payload.watched and existing is None:
                session.add(EpisodeProgress(media_id=item_id, season=payload.season, episode=payload.episode))
            elif not payload.watched and existing is not None:
                session.delete(existing)
            session.commit()
            return {"season": payload.season, "episode": payload.episode, "watched": payload.watched}

    @router.put("/api/media/{item_id}/seasons")
    def set_season(item_id: int, payload: SeasonChange):
        """An explicit episode count is required; we do not invent season lengths."""
        with Session(engine) as session:
            require_series(session, item_id)
            existing = session.scalars(select(EpisodeProgress).where(
                EpisodeProgress.media_id == item_id, EpisodeProgress.season == payload.season)).all()
            indexed = {entry.episode: entry for entry in existing}
            for episode in range(1, payload.episode_count + 1):
                entry = indexed.get(episode)
                if payload.watched and entry is None:
                    session.add(EpisodeProgress(media_id=item_id, season=payload.season, episode=episode))
                elif not payload.watched and entry is not None:
                    session.delete(entry)
            session.commit()
            return {"season": payload.season, "episode_count": payload.episode_count, "watched": payload.watched}

    @router.delete("/api/media/{item_id}/episodes")
    def clear_progress(item_id: int):
        with Session(engine) as session:
            require_series(session, item_id)
            entries = session.scalars(select(EpisodeProgress).where(EpisodeProgress.media_id == item_id)).all()
            for entry in entries:
                session.delete(entry)
            session.commit()
            return {"deleted": len(entries)}

    return router, EpisodeProgress
