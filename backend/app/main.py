"""Cinearis API: manual catalog, metadata search and watch progress."""
import os
from contextlib import asynccontextmanager
from datetime import datetime
import json
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import DateTime, Integer, String, UniqueConstraint, create_engine, func, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.analysis import router as analysis_router

from app.metadata import router as metadata_router, provider_detail, provider_search
from app.collection import build_collection_router, duplicate_for
from app.jellyfin import build_router as build_jellyfin_router
from app.instagram import build_instagram_router

VERSION = "0.6.0"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cinearis.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class MediaItem(Base):
    __tablename__ = "media_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(25), default="wishlist", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Added in v0.1.1
    provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    provider_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String(600), nullable=True)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    aliases_json: Mapped[str | None] = mapped_column(String(3000), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    watch_state: Mapped[str] = mapped_column(String(25), nullable=False, server_default="unwatched")
    season_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    episode_number: Mapped[int | None] = mapped_column(Integer, nullable=True)


class MediaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    kind: Literal["movie", "series", "anime"]
    status: Literal["wishlist", "planned", "processing", "owned", "ignored"] = "wishlist"
    provider: Literal["tmdb", "anilist"] | None = None
    provider_id: str | None = Field(default=None, max_length=60)
    poster_url: str | None = Field(default=None, max_length=600)
    release_year: int | None = Field(default=None, ge=1870, le=2200)
    original_title: str | None = Field(default=None, max_length=300)
    aliases: list[str] = Field(default_factory=list, max_length=30)
    description: str | None = Field(default=None, max_length=1500)

    @model_validator(mode="after")
    def validate_provider(self):
        if (self.provider is None) != (self.provider_id is None):
            raise ValueError("provider und provider_id müssen gemeinsam angegeben werden")
        return self


class MetadataLink(BaseModel):
    provider: Literal["tmdb", "anilist"]
    provider_id: str = Field(min_length=1, max_length=60)


class WatchUpdate(BaseModel):
    watch_state: Literal["unwatched", "completed", "through_episode", "season_completed"]
    season_number: int | None = Field(default=None, ge=1, le=999)
    episode_number: int | None = Field(default=None, ge=1, le=99999)


class StatusUpdate(BaseModel):
    status: Literal["wishlist", "planned", "processing", "owned", "ignored"]


def as_dict(item: MediaItem):
    return {
        "id": item.id, "title": item.title, "kind": item.kind,
        "status": item.status, "provider": item.provider,
        "provider_id": item.provider_id, "poster_url": item.poster_url,
        "release_year": item.release_year, "original_title": item.original_title,
        "aliases": json.loads(item.aliases_json or "[]"), "description": item.description,
        "watch_state": item.watch_state,
        "season_number": item.season_number, "episode_number": item.episode_number,
    }


collection_router, EpisodeProgress = build_collection_router(Base, MediaItem, engine, as_dict)
jellyfin_router, JellyfinEntry, JellyfinSync, resolve_jellyfin = build_jellyfin_router(Base, MediaItem, engine)
instagram_router, SourceMedia = build_instagram_router(Base, MediaItem, engine)


def migrate_v011():
    """Add nullable/defaulted columns to existing v0.1.0 installations, without deleting data."""
    columns = {col["name"] for col in inspect(engine).get_columns("media_items")}
    additions = {
        "provider": "VARCHAR(20)",
        "provider_id": "VARCHAR(60)",
        "poster_url": "VARCHAR(600)",
        "release_year": "INTEGER",
        "watch_state": "VARCHAR(25) NOT NULL DEFAULT 'unwatched'",
        "season_number": "INTEGER",
        "episode_number": "INTEGER",
        "original_title": "VARCHAR(300)",
        "aliases_json": "VARCHAR(3000)",
        "description": "VARCHAR(1500)",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE media_items ADD COLUMN {name} {definition}"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_v011()
    yield


app = FastAPI(title="Cinearis API", version=VERSION, lifespan=lifespan)
app.include_router(analysis_router)
app.include_router(metadata_router)
app.include_router(collection_router)
app.include_router(jellyfin_router)
app.include_router(instagram_router)


@app.get("/api/live")
def live():
    return {"status": "ok", "app": "Cinearis", "version": VERSION}


@app.get("/api/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok", "database": "connected", "version": VERSION}


@app.get("/api/dashboard")
def dashboard():
    with Session(engine) as session:
        items = session.scalars(select(MediaItem)).all()
        return {
            "total": len(items),
            "movies": sum(item.kind == "movie" for item in items),
            "series": sum(item.kind == "series" for item in items),
            "anime": sum(item.kind == "anime" for item in items),
            "owned": sum(item.status == "owned" for item in items),
            "missing": sum(item.status != "owned" for item in items),
            "completed": sum(item.watch_state == "completed" for item in items),
        }


@app.get("/api/media")
def list_media():
    with Session(engine) as session:
        items = session.scalars(select(MediaItem).order_by(MediaItem.id.desc()).limit(1000)).all()
        return [as_dict(item) for item in items]


@app.post("/api/media", status_code=201)
def create_media(payload: MediaCreate):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Titel darf nicht leer sein")
    with Session(engine) as session:
        matching = duplicate_for(session, MediaItem, title=title, kind=payload.kind, provider=payload.provider, provider_id=payload.provider_id)
        if matching:
            raise HTTPException(status_code=409, detail="Dieser Titel ist bereits in deiner Sammlung")
        data = payload.model_dump(exclude={"aliases"})
        data.update({"title": title, "aliases_json": json.dumps(payload.aliases[:30], ensure_ascii=False)[:3000]})
        item = MediaItem(**data)
        session.add(item)
        session.commit()
        session.refresh(item)
        return as_dict(item)



@app.patch("/api/media/{item_id}/metadata")
async def link_metadata(item_id: int, payload: MetadataLink):
    """User-confirmed external metadata association; never overwrite watch progress."""
    with Session(engine) as session:
        item = session.get(MediaItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Titel nicht gefunden")
        kind = item.kind
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            result = await provider_detail(payload.provider, payload.provider_id, kind, client)
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Metadatenanbieter nicht erreichbar") from exc
    with Session(engine) as session:
        item = session.get(MediaItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Titel nicht gefunden")
        existing = session.scalar(select(MediaItem).where(
            MediaItem.id != item_id, MediaItem.kind == item.kind,
            MediaItem.provider == result["provider"], MediaItem.provider_id == result["provider_id"],
        ))
        if existing:
            raise HTTPException(status_code=409, detail="Diese Anbieter-ID wird bereits von einem anderen Titel verwendet")
        item.title = result["title"]
        item.original_title = result["original_title"]
        item.aliases_json = json.dumps(result["aliases"], ensure_ascii=False)[:3000]
        item.description = result.get("description")
        item.release_year = result["release_year"]
        item.poster_url = result["poster_url"]
        item.provider = result["provider"]
        item.provider_id = result["provider_id"]
        session.commit()
        session.refresh(item)
        return as_dict(item)


@app.patch("/api/media/{item_id}/watch")
def update_watch(item_id: int, payload: WatchUpdate):
    with Session(engine) as session:
        item = session.get(MediaItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Titel nicht gefunden")
        state = payload.watch_state
        if item.kind == "movie" and state not in ("unwatched", "completed"):
            raise HTTPException(status_code=422, detail="Filme unterstützen nur gesehen oder nicht gesehen")
        if state == "through_episode" and (payload.season_number is None or payload.episode_number is None):
            raise HTTPException(status_code=422, detail="Staffel und Folge sind erforderlich")
        if state == "season_completed" and payload.season_number is None:
            raise HTTPException(status_code=422, detail="Staffel ist erforderlich")
        item.watch_state = state
        item.season_number = payload.season_number if state in ("through_episode", "season_completed") else None
        item.episode_number = payload.episode_number if state == "through_episode" else None
        session.commit()
        session.refresh(item)
        return as_dict(item)


@app.patch("/api/media/{item_id}/status")
def update_status(item_id: int, payload: StatusUpdate):
    with Session(engine) as session:
        item = session.get(MediaItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Titel nicht gefunden")
        item.status = payload.status
        session.commit()
        session.refresh(item)
        return as_dict(item)


@app.delete("/api/media/{item_id}", status_code=204)
def delete_media(item_id: int):
    with Session(engine) as session:
        item = session.get(MediaItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Titel nicht gefunden")
        for entry in session.scalars(select(EpisodeProgress).where(EpisodeProgress.media_id == item_id)).all():
            session.delete(entry)
        for link in session.scalars(select(SourceMedia).where(SourceMedia.media_id == item_id)).all():
            session.delete(link)
        session.delete(item)
        session.commit()


ANILIST_QUERY = """
query ($search: String) {
  Page(page: 1, perPage: 15) {
    media(search: $search, type: ANIME) {
      id
      title { english romaji native }
      startDate { year }
      coverImage { medium }
      format
    }
  }
}
"""


@app.get("/api/search")
async def search_media(q: str = Query(min_length=2, max_length=120), kind: Literal["movie", "series", "anime"] = "movie"):
    q = q.strip()
    if len(q) < 2:
        raise HTTPException(status_code=422, detail="Mindestens zwei Zeichen erforderlich")
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            if kind == "anime":
                response = await client.post("https://graphql.anilist.co", json={
                    "query": ANILIST_QUERY, "variables": {"search": q}
                })
                response.raise_for_status()
                media = response.json().get("data", {}).get("Page", {}).get("media", [])
                return [{
                    "title": m["title"].get("english") or m["title"].get("romaji") or m["title"].get("native") or "Unbekannt",
                    "kind": "anime", "provider": "anilist", "provider_id": str(m["id"]),
                    "poster_url": m.get("coverImage", {}).get("medium"),
                    "release_year": m.get("startDate", {}).get("year"),
                } for m in media]
            api_key = os.getenv("TMDB_API_KEY", "").strip()
            if not api_key:
                raise HTTPException(status_code=503, detail="TMDB_API_KEY fehlt. Bitte in .env hinterlegen oder Titel manuell hinzufügen.")
            tmdb_kind = "movie" if kind == "movie" else "tv"
            response = await client.get(
                f"https://api.themoviedb.org/3/search/{tmdb_kind}",
                params={"api_key": api_key, "query": q, "language": "de-DE", "include_adult": "false"},
            )
            response.raise_for_status()
            media = response.json().get("results", [])[:15]
            return [{
                "title": m.get("title" if kind == "movie" else "name", "Unbekannt"),
                "kind": kind, "provider": "tmdb", "provider_id": str(m["id"]),
                "poster_url": "https://image.tmdb.org/t/p/w185" + m["poster_path"] if m.get("poster_path") else None,
                "release_year": int(date[:4]) if (date := m.get("release_date" if kind == "movie" else "first_air_date", ""))[:4].isdigit() else None,
            } for m in media]
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Der Metadatenanbieter ist derzeit nicht erreichbar") from exc
