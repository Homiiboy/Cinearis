"""ForgeCore handoff: explicit download/export, never initiate external downloads.

Data reflects the latest Jellyfin scan, otherwise the manually owned state.
"""
import csv
import io
import json
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
