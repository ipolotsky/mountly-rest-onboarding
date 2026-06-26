from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.database import Base


def now_utc() -> datetime:
    return datetime.now(UTC)


class JsonColumn(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class Onboarding(Base):
    __tablename__ = "onboarding"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )
    locale: Mapped[str] = mapped_column(String(8), default="fr")
    device: Mapped[str] = mapped_column(String(16), default="desktop")
    step: Mapped[int] = mapped_column(Integer, default=1)

    confirmed: Mapped[dict] = mapped_column(JsonColumn, default=dict)
    legal: Mapped[dict] = mapped_column(JsonColumn, default=dict)
    banking: Mapped[dict] = mapped_column(JsonColumn, default=dict)
    menu: Mapped[dict] = mapped_column(JsonColumn, default=dict)

    published: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    csat: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Event(Base):
    __tablename__ = "event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(64), index=True)
    onboarding_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device: Mapped[str | None] = mapped_column(String(16), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    props: Mapped[dict] = mapped_column(JsonColumn, default=dict)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class StoredFile(Base):
    __tablename__ = "stored_file"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    onboarding_id: Mapped[str] = mapped_column(String(64), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(16))
    path: Mapped[str] = mapped_column(String(512))
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
