import enum
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Integer, Numeric, String, Index
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class TrackerKind(str, enum.Enum):
    crypto = "crypto"
    fx = "fx"

class Direction(str, enum.Enum):
    gte = "gte"
    lte = "lte"

class Tracker(Base):
    __tablename__ = "trackers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    tg_user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    kind: Mapped[TrackerKind] = mapped_column(Enum(TrackerKind, name="tracker_kind"), index=True)


    coin_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


    base: Mapped[str] = mapped_column(String(16))
    quote: Mapped[str] = mapped_column(String(16))

    direction: Mapped[Direction] = mapped_column(Enum(Direction, name="direction"))
    target: Mapped[float] = mapped_column(Numeric(20, 8))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    last_price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

Index("ix_trackers_user_active", Tracker.tg_user_id, Tracker.is_active)
