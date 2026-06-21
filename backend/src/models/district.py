# backend/src/models/district.py
from sqlalchemy import Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.database.connection import Base


class District(Base):
    __tablename__ = "districts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[str] = mapped_column(String(50), default="hanoi")
    name: Mapped[str] = mapped_column(String(100))
    geojson: Mapped[dict | None] = mapped_column(JSON, nullable=True)
