"""Phase 7 analytics: live aggregation of local collection, Jellyfin snapshot and sources."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

def build_insights_router(MediaItem, EpisodeProgress, InstagramSource, SourceMedia,
                          JellyfinEntry, JellyfinSync, engine, resolve_jellyfin):
    router = APIRouter(prefix="/api/insights", tags=["insights"])

    @router.get("")
    def insights():
        with Session(engine) as session:
            media = session.scalars(select(MediaItem)).all()
            sources = session.scalars(select(InstagramSource)).all()
            links = session.scalars(select(SourceMedia)).all()
            episodes = session.scalars(select(EpisodeProgress)).all()
            sync = session.scalar(select(JellyfinSync).order_by(JellyfinSync.id.desc()))
            jelly_entries = session.scalars(select(JellyfinEntry)).all() if sync else []

        kinds = Counter(item.kind for item in media)
        statuses = Counter(item.status for item in media)
        watch = Counter(item.watch_state for item in media)
        source_count = Counter(link.media_id for link in links)
        id_to_media = {item.id: item for item in media}
        sources_by_id = {src.id: src for src in sources}
        episodes_by_media = Counter(ep.media_id for ep in episodes)
        discovered = sorted(
            [{"id": item.id, "title": item.title, "kind": item.kind,
              "poster_url": item.poster_url, "mentions": count,
              "watched_episodes": episodes_by_media.get(item.id, 0)}
             for item_id, count in source_count.items()
             if (item := id_to_media.get(item_id))],
            key=lambda row: (-row["mentions"], row["title"].casefold(), row["id"])
        )
        source_stats = Counter(source.kind for source in sources)
        top_sources = sorted(
            [{"id": src.id, "url": src.url, "kind": src.kind, "titles": count}
             for source_id, count in Counter(link.source_id for link in links).items()
             if (src := sources_by_id.get(source_id))],
            key=lambda row: (-row["titles"], row["id"])
        )

        jf_status = Counter()
        jf_matches = []
        if sync:
            jf_media = [entry for entry in jelly_entries if entry.media_type in ("movie", "series")]
            jf_episodes = [entry for entry in jelly_entries if entry.media_type == "episode"]
            for item in media:
                match = resolve_jellyfin(item, jf_media, jf_episodes)
                jf_status[match["status"]] += 1
                jf_matches.append({"media_id": item.id, "title": item.title,
                                   "status": match["status"],
                                   "episodes_found": match.get("episodes_found", 0)})
        monthly = Counter()
        for item in media:
            created = item.created_at
            if created:
                monthly[created.strftime("%Y-%m")] += 1
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "collection": {
                "total": len(media),
                "kinds": {k: kinds.get(k, 0) for k in ("movie", "series", "anime")},
                "statuses": {k: statuses.get(k, 0) for k in ("wishlist", "planned", "processing", "owned", "ignored")},
                "watch_states": {k: watch.get(k, 0) for k in ("unwatched", "completed", "through_episode", "season_completed")},
                "tracked_episodes": len(episodes),
                "titles_with_episode_tracking": len(episodes_by_media),
                "monthly_added": [{"month": k, "count": v} for k, v in sorted(monthly.items())],
            },
            "jellyfin": {
                "synced": bool(sync),
                "last_sync": sync.synced_at.isoformat() if sync else None,
                "counts": {
                    "movies": sync.movie_count if sync else 0,
                    "series": sync.series_count if sync else 0,
                    "episodes": sync.episode_count if sync else 0,
                },
                "match_status": {k: jf_status.get(k, 0) for k in ("present", "series_only", "missing", "ambiguous")},
                "matches": jf_matches,
            },
            "instagram": {
                "sources": len(sources),
                "kinds": {k: source_stats.get(k, 0) for k in ("post", "reel", "video")},
                "unique_titles": len(source_count),
                "total_mentions": len(links),
                "most_mentioned": discovered[:20],
                "top_sources": top_sources[:15],
            },
            "notes": [
                "Fundhäufigkeit zählt eindeutige Titel-Quellen-Verknüpfungen, nicht Aufrufe oder Likes.",
                "Jellyfin-Werte beruhen auf dem letzten erfolgreichen Scan und sind keine Live-Verfügbarkeitsprüfung.",
                "Getrackte Episoden sind manuell markiert und entsprechen nicht automatisch Jellyfin-Abspielständen.",
            ],
        }
    return router
