"""Pure read-only Jellyfin matching tests using isolated SQLite fixtures."""
import unittest
from sqlalchemy import DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.jellyfin import build_router


class Base(DeclarativeBase): pass


class Media(Base):
    __tablename__ = "media_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(300))
    original_title: Mapped[str | None] = mapped_column(String(300))
    aliases_json: Mapped[str | None] = mapped_column(String(3000))
    provider: Mapped[str | None] = mapped_column(String(20))
    provider_id: Mapped[str | None] = mapped_column(String(60))
    release_year: Mapped[int | None] = mapped_column(Integer)


class JellyfinMatchingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        _, cls.Entry, _, cls.resolve = build_router(Base, Media, cls.engine)
        Base.metadata.create_all(cls.engine)

    def entry(self, **kwargs):
        defaults=dict(jellyfin_id="abc", media_type="series",name="One Piece",tmdb_id=None,imdb_id=None,
                      year=1999,series_id=None,season_number=None,episode_number=None,episode_end=None,original_title=None)
        defaults.update(kwargs)
        return self.Entry(**defaults)

    def media(self, **kwargs):
        defaults=dict(id=1,kind="anime",title="One Piece",original_title=None,aliases_json="[]",provider=None,
                      provider_id=None,release_year=1999)
        defaults.update(kwargs)
        return Media(**defaults)

    def test_name_match_sees_only_own_episodes(self):
        entries=[self.entry(),self.entry(jellyfin_id="xyz",name="Naruto")]
        episodes=[self.entry(jellyfin_id="e1",media_type="episode",series_id="abc",season_number=1,episode_number=1),
                  self.entry(jellyfin_id="e2",media_type="episode",series_id="xyz",season_number=1,episode_number=2)]
        result=self.resolve(self.media(),entries,episodes)
        self.assertEqual(result["episodes_found"],1)
        self.assertEqual(result["seasons"]["1"],[1])

    def test_tmdb_id_preferred(self):
        entries=[self.entry(jellyfin_id="a",name="Different",tmdb_id="123"),
                 self.entry(jellyfin_id="b",name="One Piece")]
        result=self.resolve(self.media(kind="series",provider="tmdb",provider_id="123"),entries,[])
        self.assertEqual(result["jellyfin_id"],"a")

    def test_ambiguous_titles_are_not_merged(self):
        entries=[self.entry(jellyfin_id="a"),self.entry(jellyfin_id="b")]
        self.assertEqual(self.resolve(self.media(),entries,[])["status"],"ambiguous")

    def test_missing(self):
        self.assertEqual(self.resolve(self.media(),[],[])["status"],"missing")

    def test_special_season(self):
        entries=[self.entry()]
        episodes=[self.entry(jellyfin_id="e",media_type="episode",series_id="abc",season_number=0,episode_number=1)]
        self.assertEqual(self.resolve(self.media(),entries,episodes)["seasons"]["0"],[1])

    def test_multi_episode_file(self):
        entries=[self.entry()]
        episodes=[self.entry(jellyfin_id="e",media_type="episode",series_id="abc",season_number=3,episode_number=1,episode_end=3)]
        self.assertEqual(self.resolve(self.media(),entries,episodes)["seasons"]["3"],[1,2,3])


if __name__ == "__main__":
    unittest.main()
