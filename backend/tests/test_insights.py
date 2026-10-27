"""Phase 7: analytics derived from isolated in-memory tables."""
import unittest
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import StaticPool
from app.insights import build_insights_router


class Base(DeclarativeBase):
    pass


class Media(Base):
    __tablename__ = "media_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    watch_state: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    poster_url: Mapped[str | None] = mapped_column(String, nullable=True)


class Episode(Base):
    __tablename__ = "episode_progress"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media_items.id"))
    season: Mapped[int] = mapped_column(Integer)
    episode: Mapped[int] = mapped_column(Integer)


class Source(Base):
    __tablename__ = "instagram_sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)


class Link(Base):
    __tablename__ = "instagram_source_media"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("instagram_sources.id"))
    media_id: Mapped[int] = mapped_column(ForeignKey("media_items.id"))


class JellyEntry(Base):
    __tablename__ = "jellyfin_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    media_type: Mapped[str] = mapped_column(String)


class JellySync(Base):
    __tablename__ = "jellyfin_sync"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime)
    movie_count: Mapped[int] = mapped_column(Integer)
    series_count: Mapped[int] = mapped_column(Integer)
    episode_count: Mapped[int] = mapped_column(Integer)


class InsightsTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                                    poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        app = FastAPI()
        app.include_router(build_insights_router(
            Media, Episode, Source, Link, JellyEntry, JellySync, self.engine,
            lambda item, entries, episodes: {"status": "missing"}))
        self.client = TestClient(app)

    def test_empty_dataset(self):
        result = self.client.get("/api/insights")
        self.assertEqual(result.status_code, 200)
        data = result.json()
        self.assertEqual(data["collection"]["total"], 0)
        self.assertEqual(data["instagram"]["total_mentions"], 0)
        self.assertFalse(data["jellyfin"]["synced"])

    def test_counts_and_sources(self):
        with Session(self.engine) as session:
            session.add_all([
                Media(id=1, title="One Piece", kind="anime", status="wishlist",
                      watch_state="through_episode", created_at=datetime(2026, 10, 1)),
                Media(id=2, title="Spirited Away", kind="movie", status="owned",
                      watch_state="completed", created_at=datetime(2026, 10, 2)),
                Source(id=1, url="https://www.instagram.com/p/ExampleA/", kind="post"),
                Source(id=2, url="https://www.instagram.com/p/ExampleB/", kind="post"),
                Link(source_id=1, media_id=1), Link(source_id=2, media_id=1),
                Link(source_id=1, media_id=2),
                Episode(media_id=1, season=1, episode=1),
                Episode(media_id=1, season=1, episode=2),
            ])
            session.commit()
        data = self.client.get("/api/insights").json()
        self.assertEqual(data["collection"]["kinds"]["anime"], 1)
        self.assertEqual(data["collection"]["watch_states"]["completed"], 1)
        self.assertEqual(data["collection"]["tracked_episodes"], 2)
        self.assertEqual(data["instagram"]["sources"], 2)
        self.assertEqual(data["instagram"]["total_mentions"], 3)
        self.assertEqual(data["instagram"]["most_mentioned"][0]["mentions"], 2)
        self.assertEqual(data["collection"]["monthly_added"], [{"month": "2026-10", "count": 2}])


if __name__ == "__main__":
    unittest.main()
