"""ForgeCore handoff: explicit download/export, never initiate external downloads.

Data reflects the latest Jellyfin scan, otherwise the manually owned state.
"""
import csv
import io
import json
import os
from urllib.parse import urlsplit
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session


def build_forgecore_router(MediaItem, JellyfinEntry, JellyfinSync, engine, resolve_jellyfin):
    router = APIRouter(prefix="/api/forgecore", tags=["forgecore"])

    def collect():
        with Session(engine) as session:
            rows = session.scalars(select(MediaItem).order_by(MediaItem.id)).all()
            latest = session.scalar(select(JellyfinSync.id).limit(1)) is not None
            library = session.scalars(select(JellyfinEntry)).all() if latest else []
            jf_titles = [x for x in library if x.media_type in ("movie", "series")]
            jf_episodes = [x for x in library if x.media_type == "episode"]
            result = []
            for media in rows:
                if media.status == "ignored":
                    continue
                match = resolve_jellyfin(media, jf_titles, jf_episodes) if latest else None
                if match and match["status"] != "missing":
                    # Avoid exporting present, series-only or ambiguous entries.
                    continue
                if not match and media.status == "owned":
                    continue
                result.append({
                    "cinearis_id": media.id,
                    "title": media.title,
                    "original_title": media.original_title or "",
                    "media_type": media.kind,
                    "release_year": media.release_year,
                    "provider": media.provider or "",
                    "provider_id": media.provider_id or "",
                    "status": media.status,
                    "library_check": "jellyfin_missing" if latest else "manual_status_only",
                })
            return result, latest


    def forgecore_config():
        endpoint = os.getenv("FORGECORE_URL", "").strip().rstrip("/")
        password = os.getenv("FORGECORE_PASSWORD", "").strip()
        if not endpoint or not password:
            return None
        url = urlsplit(endpoint)
        if (url.scheme not in ("http", "https") or not url.hostname
                or url.username or url.password or url.query or url.fragment):
            raise HTTPException(status_code=503, detail="FORGECORE_URL ist ungültig")
        # URL is a server administrator-controlled environment setting, not user input.
        return endpoint, password

    @router.get("/connection")
    def connection():
        return {"configured": forgecore_config() is not None,
                "mode": "watchlist_only", "downloads_enabled": False}

    @router.post("/watchlist/{media_id}")
    async def send_to_watchlist(media_id: int):
        """Opt-in transfer of one TMDB item into ForgeCore's non-monitored watchlist."""
        config = forgecore_config()
        if not config:
            raise HTTPException(status_code=503, detail="FORGECORE_URL / FORGECORE_PASSWORD fehlen")
        rows, _ = collect()
        entry = next((row for row in rows if row["cinearis_id"] == media_id), None)
        if entry is None:
            raise HTTPException(status_code=409, detail="Titel ist nicht eindeutig als fehlend freigegeben")
        if entry["provider"] != "tmdb" or not str(entry["provider_id"]).isdigit():
            raise HTTPException(status_code=422, detail="Für ForgeCore wird eine gültige TMDB-ID benötigt")
        kind = "movie" if entry["media_type"] == "movie" else "tv"
        base, password = config
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
                login = await client.post(base + "/api/auth/login", headers={
                    "X-ForgeCore-Request": "1",
                }, json={"password": password})
                login.raise_for_status()
                csrf = login.json().get("csrf", "")
                if not isinstance(csrf, str) or len(csrf) != 48:
                    raise ValueError("Ungültige ForgeCore-Anmeldung")
                response = await client.post(base + "/api/discover/watchlist", headers={
                    "X-ForgeCore-CSRF": csrf,
                    "X-ForgeCore-Request": "1",
                }, json={"kind": kind, "id": int(entry["provider_id"]), "monitored": False})
                response.raise_for_status()
                result = response.json()
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError, KeyError, TypeError) as exc:
            # Never put credentials, cookies or provider response bodies into user-visible errors.
            raise HTTPException(status_code=502, detail="ForgeCore-Anmeldung oder Merkliste fehlgeschlagen") from exc
        return {"sent": True, "cinearis_id": media_id, "kind": kind,
                "tmdb_id": entry["provider_id"], "monitored": False,
                "forgecore_title": (result.get("item") or {}).get("title", entry["title"])}

    @router.get("/preview")
    def preview():
        rows, synced = collect()
        return {"items": rows, "count": len(rows), "jellyfin_snapshot": synced,
                "disclaimer": "Export only; no automatic download or ForgeCore API action."}

    @router.get("/export")
    def export(format: str = "json"):
        if format not in ("json", "csv"):
            raise HTTPException(status_code=422, detail="format muss json oder csv sein")
        rows, synced = collect()
        filename = f"cinearis-forgecore-{datetime.now(timezone.utc):%Y%m%d}"
        if format == "json":
            payload = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
                       "jellyfin_snapshot": synced, "items": rows}
            return Response(content=json.dumps(payload, ensure_ascii=False, indent=2),
                            media_type="application/json; charset=utf-8",
                            headers={"Content-Disposition": f'attachment; filename="{filename}.json"',
                                     "Cache-Control": "no-store"})
        output = io.StringIO()
        fields = ["cinearis_id", "title", "original_title", "media_type", "release_year",
                  "provider", "provider_id", "status", "library_check"]
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        return Response(content="\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"',
                                 "Cache-Control": "no-store"})
    return router
