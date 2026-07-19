# backend/src/models/event.py
from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.database.connection import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (Index("idx_events_district_start", "district_id", "start_time"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[str] = mapped_column(String(50), default="hanoi")
    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    impact_level: Mapped[str] = mapped_column(String(20), default="low")
