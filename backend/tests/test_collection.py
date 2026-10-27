import unittest
from app.collection import canon, duplicate_for
from sqlalchemy import create_engine, String, Integer, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

class Base(DeclarativeBase): pass
class Item(Base):
    __tablename__="media_items"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    kind:Mapped[str]=mapped_column(String)
    title:Mapped[str]=mapped_column(String)
    original_title:Mapped[str|None]=mapped_column(String,nullable=True)
    aliases_json:Mapped[str|None]=mapped_column(String,nullable=True)
    provider:Mapped[str|None]=mapped_column(String,nullable=True)
    provider_id:Mapped[str|None]=mapped_column(String,nullable=True)

class DuplicateTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            session.add(Item(kind="movie",title="Der König der Löwen",original_title="The Lion King",aliases_json='["Lion King"]',provider="tmdb",provider_id="8587"))
            session.commit()

    def test_alias_match(self):
        with Session(self.engine) as session:
            self.assertIsNotNone(duplicate_for(session,Item,title="The Lion King",kind="movie"))

    def test_normalized_title(self):
        self.assertEqual(canon("König der Löwen"),"konigderlowen")

    def test_other_type_is_not_duplicate(self):
        with Session(self.engine) as session:
            self.assertIsNone(duplicate_for(session,Item,title="Lion King",kind="anime"))

    def test_provider_identity(self):
        with Session(self.engine) as session:
            self.assertIsNotNone(duplicate_for(session,Item,title="Anything",kind="movie",provider="tmdb",provider_id="8587"))

if __name__=="__main__":
    unittest.main()
