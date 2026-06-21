# backend/src/models/feedback.py
from datetime import datetime
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.database.connection import Base


class CitizenFeedback(Base):
    __tablename__ = "citizen_feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[str] = mapped_column(String(50), default="hanoi")
    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id"), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
