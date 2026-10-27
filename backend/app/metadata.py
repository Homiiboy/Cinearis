"""Search and resolve media metadata from TMDB and AniList.

Provider identity is always preserved. Results are suggestions, not verified matches
until a user chooses one.
"""
import os
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/metadata", tags=["metadata"])

ANILIST_SEARCH = """
query ($search: String) {
 Page(page: 1, perPage: 15) {
  media(search: $search, type: ANIME, isAdult: false) {
   id title { english romaji native }
   synonyms startDate { year } coverImage { medium } description(asHtml: false)
  }
 }
}
"""
ANILIST_DETAIL = """
query ($id: Int) {
 Media(id: $id, type: ANIME) {
  id title { english romaji native }
  synonyms startDate { year } coverImage { medium } description(asHtml: false)
 }
}
"""


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"\w+", value))


def relevance(query: str, names: list[str]) -> float:
    query_norm = normalized(query)
    if not query_norm:
        return 0
    scores = []
    for name in names:
        other = normalized(name)
        if not other:
            continue
        score = SequenceMatcher(None, query_norm, other).ratio()
        if query_norm == other:
            score = 1.0
        elif other.startswith(query_norm + " "):
            score = max(score, 0.9)
        scores.append(score)
    return round(max(scores, default=0), 3)


def cleaned_names(*values: object) -> list[str]:
    names = []
    for value in values:
        if isinstance(value, list):
            names.extend(cleaned_names(*value))
        elif isinstance(value, str) and value.strip() and value.strip() not in names:
            names.append(value.strip())
    return list(dict.fromkeys(names))[:30]


def anime_result(item: dict) -> dict:
    title = item.get("title") or {}
    names = cleaned_names(title.get("english"), title.get("romaji"), title.get("native"), item.get("synonyms", []))
    return {
        "title": names[0] if names else "Unbekannt",
        "original_title": title.get("romaji") or title.get("native") or names[0] if names else "Unbekannt",
        "aliases": names,
        "kind": "anime", "provider": "anilist", "provider_id": str(item["id"]),
        "poster_url": (item.get("coverImage") or {}).get("medium"),
        "release_year": (item.get("startDate") or {}).get("year"),
        "description": (item.get("description") or "")[:1200],
    }


def tmdb_result(item: dict, kind: str) -> dict:
    primary = "title" if kind == "movie" else "name"
    original = "original_title" if kind == "movie" else "original_name"
    names = cleaned_names(item.get(primary), item.get(original))
    date = item.get("release_date" if kind == "movie" else "first_air_date") or ""
    return {
        "title": item.get(primary) or item.get(original) or "Unbekannt",
        "original_title": item.get(original) or item.get(primary) or "Unbekannt",
        "aliases": names,
        "kind": kind, "provider": "tmdb", "provider_id": str(item["id"]),
        "poster_url": "https://image.tmdb.org/t/p/w342" + item["poster_path"] if item.get("poster_path") else None,
        "release_year": int(date[:4]) if date[:4].isdigit() else None,
        "description": (item.get("overview") or "")[:1200],
    }


async def provider_search(query: str, kind: Literal["movie", "series", "anime"], client: httpx.AsyncClient) -> list[dict]:
    if kind == "anime":
        response = await client.post("https://graphql.anilist.co", json={
            "query": ANILIST_SEARCH, "variables": {"search": query}
        })
        response.raise_for_status()
        data = response.json()
        if data.get("errors"):
            raise ValueError("AniList returned errors")
        items = data.get("data", {}).get("Page", {}).get("media") or []
        return [anime_result(item) for item in items]
    api_key = os.getenv("TMDB_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="TMDB_API_KEY fehlt. Titel können weiterhin manuell gespeichert werden.")
    media_type = "movie" if kind == "movie" else "tv"
    response = await client.get(f"https://api.themoviedb.org/3/search/{media_type}", params={
        "api_key": api_key, "query": query, "language": "de-DE", "include_adult": "false",
    })
    response.raise_for_status()
    return [tmdb_result(item, kind) for item in response.json().get("results", [])[:15]]


async def provider_detail(provider: Literal["tmdb", "anilist"], provider_id: str,
                          kind: Literal["movie", "series", "anime"], client: httpx.AsyncClient) -> dict:
    if not provider_id.isdigit() or len(provider_id) > 15:
        raise HTTPException(status_code=422, detail="Ungültige Anbieter-ID")
    if kind == "anime" and provider == "anilist":
        response = await client.post("https://graphql.anilist.co", json={
            "query": ANILIST_DETAIL, "variables": {"id": int(provider_id)}
        })
        response.raise_for_status()
        item = response.json().get("data", {}).get("Media")
        if not item:
            raise HTTPException(status_code=404, detail="Titel nicht gefunden")
        return anime_result(item)
    if kind not in ("movie", "series") or provider != "tmdb":
        raise HTTPException(status_code=422, detail="Unpassender Metadatenanbieter")
    key = os.getenv("TMDB_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="TMDB_API_KEY fehlt")
    category = "movie" if kind == "movie" else "tv"
    response = await client.get(f"https://api.themoviedb.org/3/{category}/{provider_id}",
                                params={"api_key": key, "language": "de-DE", "append_to_response": "alternative_titles"})
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Titel nicht gefunden")
    response.raise_for_status()
    item = response.json()
    result = tmdb_result(item, kind)
    alternatives = item.get("alternative_titles") or {}
    additional = [v.get("title") for v in alternatives.get("titles", [])] if kind == "movie" else [v.get("title") for v in alternatives.get("results", [])]
    result["aliases"] = cleaned_names(result["aliases"], additional)
    return result


@router.get("/search")
async def search_metadata(q: str = Query(min_length=2, max_length=120),
                          kind: Literal["movie", "series", "anime"] = "movie"):
    q = q.strip()
    if len(q) < 2:
        raise HTTPException(status_code=422, detail="Mindestens zwei Zeichen erforderlich")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            data = await provider_search(q, kind, client)
        for item in data:
            item["match_score"] = relevance(q, item["aliases"])
        return sorted(data, key=lambda item: item["match_score"], reverse=True)
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Metadatensuche derzeit nicht erreichbar") from exc


@router.get("/detail")
async def metadata_detail(provider: Literal["tmdb", "anilist"],
                          provider_id: str = Query(min_length=1, max_length=60),
                          kind: Literal["movie", "series", "anime"] = "movie"):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            return await provider_detail(provider, provider_id, kind, client)
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Metadatendetails derzeit nicht erreichbar") from exc
