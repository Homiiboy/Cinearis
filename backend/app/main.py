"""Cinearis v0.1.0 backend: foundational health and catalog API."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import Integer, String, DateTime, func

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
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Cinearis API", version="0.1.0", lifespan=lifespan)


@app.get("/api/live")
def live():
    return {"status": "ok", "app": "Cinearis", "version": "0.1.0"}


@app.get("/api/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok", "database": "connected", "version": "0.1.0"}


@app.get("/api/dashboard")
def dashboard():
    try:
        with Session(engine) as session:
            items = session.scalars(select(MediaItem)).all()
            return {
                "total": len(items),
                "movies": sum(item.kind == "movie" for item in items),
                "series": sum(item.kind == "series" for item in items),
                "anime": sum(item.kind == "anime" for item in items),
                "owned": sum(item.status == "owned" for item in items),
                "missing": sum(item.status != "owned" for item in items),
            }
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@app.get("/api/media")
def list_media():
    with Session(engine) as session:
        items = session.scalars(select(MediaItem).order_by(MediaItem.id.desc()).limit(200)).all()
        return [
            {"id": item.id, "title": item.title, "kind": item.kind, "status": item.status}
            for item in items
        ]
