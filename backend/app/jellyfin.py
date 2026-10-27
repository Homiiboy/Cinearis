"""Read-only Jellyfin library synchronisation and deterministic matching.

No Jellyfin credentials are exposed through the API.
All requests use a fixed administrator-configured URL (environment variables).
"""
from datetime import datetime, timezone
import os
import re
import unicodedata
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, HTTPException
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

MAX_ITEMS = 50000
PAGE_SIZE = 500


def canonical(value: str) -> str:
    value = unicodedata.normalize("NFKD", (value or "").casefold())
    return re.sub(r"[^a-z0-9]+", "", "".join(c for c in value if not unicodedata.combining(c)))


def get_config():
    url = os.getenv("JELLYFIN_URL", "").strip().rstrip("/")
    key = os.getenv("JELLYFIN_API_KEY", "").strip()
    if not url or not key:
        return None
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise HTTPException(status_code=503, detail="JELLYFIN_URL ist ungültig")
    return url, key


def jellyfin_headers(key: str):
    return {"X-Emby-Token": key, "Accept": "application/json"}


def build_router(Base, MediaItem, engine):
    class JellyfinEntry(Base):
        __tablename__ = "jellyfin_entries"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        jellyfin_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
        media_type: Mapped[str] = mapped_column(String(12), nullable=False)
        name: Mapped[str] = mapped_column(String(300), nullable=False)
        year: Mapped[int | None] = mapped_column(Integer)
        tmdb_id: Mapped[str | None] = mapped_column(String(60))
        imdb_id: Mapped[str | None] = mapped_column(String(60))
        series_id: Mapped[str | None] = mapped_column(String(100))
        season_number: Mapped[int | None] = mapped_column(Integer)
        episode_number: Mapped[int | None] = mapped_column(Integer)
        episode_end: Mapped[int | None] = mapped_column(Integer)
        original_title: Mapped[str | None] = mapped_column(String(300))

    class JellyfinSync(Base):
        __tablename__ = "jellyfin_sync"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        movie_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
        series_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
        episode_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    router = APIRouter(prefix="/api/jellyfin", tags=["jellyfin"])

    def resolve(media, entries, episodes):
        """Exact ID preferred. Name/year is fallback only if unique and unambiguous."""
        exact = []
        for entry in entries:
            if entry.media_type != ("movie" if media.kind == "movie" else "series"):
                continue
            if media.provider == "tmdb" and media.provider_id and entry.tmdb_id == media.provider_id:
                exact.append(entry)
        if len(exact) == 1:
            match, method = exact[0], "tmdb"
        elif len(exact) > 1:
            return {"status": "ambiguous", "reason": "Mehrere Jellyfin-Einträge mit derselben TMDB-ID"}
        else:
            aliases = [media.title, media.original_title or ""]
            try:
                import json
                aliases += json.loads(media.aliases_json or "[]")
            except (ValueError, TypeError):
                pass
            lookup = {canonical(name) for name in aliases if name}
            candidates = [entry for entry in entries if
                          entry.media_type == ("movie" if media.kind == "movie" else "series") and
                          (canonical(entry.name) in lookup or canonical(entry.original_title or "") in lookup) and
                          (not media.release_year or not entry.year or abs(media.release_year - entry.year) <= 1)]
            if len(candidates) == 1:
                match, method = candidates[0], "name"
            elif len(candidates) > 1:
                return {"status": "ambiguous", "reason": "Mehrere ähnliche Jellyfin-Titel gefunden"}
            else:
                return {"status": "missing"}
        if media.kind == "movie":
            return {"status": "present", "match_method": method, "jellyfin_id": match.jellyfin_id,
                    "matched_title": match.name}
        relevant = [e for e in episodes if e.series_id == match.jellyfin_id and
                    e.season_number is not None and e.episode_number is not None]
        by_season = {}
        for e in relevant:
            season = str(e.season_number)
            values = by_season.setdefault(season, set())
            end = e.episode_end if e.episode_end is not None else e.episode_number
            # Jellyfin may represent files containing multiple episodes.
            if end < e.episode_number or end - e.episode_number > 15:
                end = e.episode_number
            values.update(range(e.episode_number, end + 1))
        return {"status": "present" if relevant else "series_only",
                "match_method": method, "jellyfin_id": match.jellyfin_id,
                "matched_title": match.name,
                "episodes_found": sum(len(v) for v in by_season.values()),
                "seasons": {k: sorted(v) for k, v in sorted(by_season.items(), key=lambda p: int(p[0]))}}

    def build_matches(session):
        entries = session.scalars(select(JellyfinEntry).where(JellyfinEntry.media_type.in_(["movie", "series"]))).all()
        episodes = session.scalars(select(JellyfinEntry).where(JellyfinEntry.media_type == "episode")).all()
        return [{"media_id": media.id, **resolve(media, entries, episodes)}
                for media in session.scalars(select(MediaItem)).all()]

    @router.get("/status")
    def status():
        configured = get_config() is not None
        with Session(engine) as session:
            snapshot = session.scalar(select(JellyfinSync).order_by(JellyfinSync.id.desc()))
            return {"configured": configured, "last_sync": snapshot.synced_at.isoformat() if snapshot else None,
                    "movie_count": snapshot.movie_count if snapshot else 0,
                    "series_count": snapshot.series_count if snapshot else 0,
                    "episode_count": snapshot.episode_count if snapshot else 0,
                    "read_only": True}

    @router.get("/matches")
    def matches():
        with Session(engine) as session:
            has_snapshot = session.scalar(select(JellyfinSync.id).limit(1)) is not None
            if not has_snapshot:
                return {"synced": False, "matches": []}
            return {"synced": True, "matches": build_matches(session)}

    @router.post("/sync")
    async def sync():
        config = get_config()
        if not config:
            raise HTTPException(status_code=503, detail="JELLYFIN_URL und JELLYFIN_API_KEY fehlen in .env")
        url, key = config
        headers = jellyfin_headers(key)
        collected = []
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
                # Check authentication before replacing the existing snapshot.
                check = await client.get(url + "/System/Info", headers=headers)
                check.raise_for_status()
                offset = 0
                while True:
                    response = await client.get(url + "/Items", headers=headers, params={
                        "Recursive": "true", "IncludeItemTypes": "Movie,Series,Episode",
                        "Fields": "ProviderIds,OriginalTitle", "StartIndex": offset,
                        "Limit": PAGE_SIZE,
                    })
                    response.raise_for_status()
                    data = response.json()
                    page = data.get("Items", [])
                    if not isinstance(page, list):
                        raise ValueError("Ungültige Jellyfin-Antwort")
                    collected.extend(page)
                    if len(collected) > MAX_ITEMS:
                        raise HTTPException(status_code=413, detail="Jellyfin-Bibliothek überschreitet das derzeitige Scanlimit")
                    offset += len(page)
                    total = data.get("TotalRecordCount")
                    if not page or (isinstance(total, int) and offset >= total) or (total is None and len(page) < PAGE_SIZE):
                        break
        except HTTPException:
            raise
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise HTTPException(status_code=502, detail="Jellyfin nicht erreichbar oder Anfrage fehlgeschlagen") from exc

        prepared = []
        for item in collected:
            category = {"Movie": "movie", "Series": "series", "Episode": "episode"}.get(item.get("Type"))
            if not category or not item.get("Id"):
                continue
            providers = item.get("ProviderIds") or {}
            prepared.append(dict(
                jellyfin_id=str(item["Id"]), media_type=category, name=str(item.get("Name") or "Ohne Titel")[:300],
                year=item.get("ProductionYear") if isinstance(item.get("ProductionYear"), int) else None,
                tmdb_id=str(providers.get("Tmdb")) if providers.get("Tmdb") else None,
                imdb_id=str(providers.get("Imdb")) if providers.get("Imdb") else None,
                series_id=str(item.get("SeriesId")) if item.get("SeriesId") else None,
                season_number=item.get("ParentIndexNumber") if isinstance(item.get("ParentIndexNumber"), int) else None,
                episode_number=item.get("IndexNumber") if isinstance(item.get("IndexNumber"), int) else None,
                episode_end=item.get("IndexNumberEnd") if isinstance(item.get("IndexNumberEnd"), int) else None,
                original_title=str(item.get("OriginalTitle"))[:300] if item.get("OriginalTitle") else None,
            ))
        # Preserve the previous snapshot if the remote scan fails; replace in one transaction.
        with Session(engine) as session:
            session.query(JellyfinEntry).delete(synchronize_session=False)
            session.add_all(JellyfinEntry(**data) for data in prepared)
            counts = {name: sum(row["media_type"] == name for row in prepared)
                      for name in ("movie", "series", "episode")}
            session.add(JellyfinSync(synced_at=datetime.now(timezone.utc), movie_count=counts["movie"],
                                    series_count=counts["series"], episode_count=counts["episode"]))
            session.commit()
            matched = build_matches(session)
        return {"success": True, "movies": counts["movie"], "series": counts["series"],
                "episodes": counts["episode"], "matched": sum(x["status"] in ("present", "series_only") for x in matched)}

    return router, JellyfinEntry, JellyfinSync, resolve
