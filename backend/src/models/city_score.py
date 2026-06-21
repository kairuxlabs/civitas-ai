# backend/src/models/city_score.py
from datetime import datetime
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.database.connection import Base


class CityScore(Base):
    __tablename__ = "city_score"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[str] = mapped_column(String(50), default="hanoi")
    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    traffic_score: Mapped[float] = mapped_column(Float, default=0)
    environment_score: Mapped[float] = mapped_column(Float, default=0)
    citizen_score: Mapped[float] = mapped_column(Float, default=0)
    risk_score: Mapped[float] = mapped_column(Float, default=0)
    overall_score: Mapped[float] = mapped_column(Float, default=0)
