"""Release-candidate handoff tests without actual ForgeCore download requests."""
import json
import unittest
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import StaticPool
from app.forgecore import build_forgecore_router


class Base(DeclarativeBase):
    pass


class Media(Base):
    __tablename__ = "media_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    original_title: Mapped[str | None] = mapped_column(String, nullable=True)
    kind: Mapped[str] = mapped_column(String)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)


class JellyEntry(Base):
    __tablename__ = "jellyfin_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    media_type: Mapped[str] = mapped_column(String)


class JellySync(Base):
    __tablename__ = "jellyfin_sync"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class ForgeCoreExportTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread":False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.engine = engine
        app = FastAPI()
        app.include_router(build_forgecore_router(Media, JellyEntry, JellySync, engine,
                                                  lambda item, titles, episodes: {"status": "missing"}))
        self.client = TestClient(app)

    def test_export_excludes_owned_and_ignored_without_snapshot(self):
        with Session(self.engine) as db:
            db.add_all([
                Media(id=1,title="Wishlist",kind="movie",status="wishlist"),
                Media(id=2,title="Already owned",kind="movie",status="owned"),
                Media(id=3,title="Ignored",kind="anime",status="ignored"),
            ])
            db.commit()
        data = self.client.get("/api/forgecore/preview").json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["items"][0]["title"], "Wishlist")
        export = self.client.get("/api/forgecore/export?format=json")
        self.assertEqual(export.status_code, 200)
        self.assertEqual(json.loads(export.content)["items"][0]["title"], "Wishlist")
        csv_response = self.client.get("/api/forgecore/export?format=csv")
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn("Wishlist", csv_response.text)

    def test_invalid_format(self):
        self.assertEqual(self.client.get("/api/forgecore/export?format=xml").status_code, 422)


if __name__ == "__main__":
    unittest.main()
