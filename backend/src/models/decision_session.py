from datetime import datetime
from sqlalchemy import Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.database.connection import Base


class DecisionSession(Base):
    __tablename__ = "decision_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    goal: Mapped[str] = mapped_column(String(500))
    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="collecting")
    decision_id: Mapped[int | None] = mapped_column(ForeignKey("agent_decisions.id"), nullable=True)
    baseline_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expected_outcome: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    observed_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    outcome_delta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    success_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    context_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    outcome_evidence: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "run_id": self.run_id, "goal": self.goal,
            "district_id": self.district_id, "status": self.status,
            "decision_id": self.decision_id,
            "baseline_scores": self.baseline_scores,
            "expected_outcome": self.expected_outcome,
            "observed_scores": self.observed_scores,
            "outcome_delta": self.outcome_delta,
            "success_rate": self.success_rate,
            "outcome_status": self.outcome_status,
            "context_snapshot": self.context_snapshot,
            "outcome_evidence": self.outcome_evidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }
