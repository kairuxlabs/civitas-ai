# backend/src/models/weather.py
from datetime import datetime
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.database.connection import Base


class Weather(Base):
    __tablename__ = "weather"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[str] = mapped_column(String(50), default="hanoi")
    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    rain: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
