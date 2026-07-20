# backend/src/runtime/workflow.py
"""Workflow runtime (spec_v2 §10): human approval gate, then
notify → create incident → store memory → done.

Persistence into the v1 agent_decisions table is best-effort: the
runtime keeps working when no database is reachable.
"""
import asyncio
from datetime import datetime, timezone

from src.runtime.event_bus import Event, EventBus, EventTypes
from src.runtime.memory import decision_memory
from src.runtime.state import RunState, RunStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowRuntime:
    def __init__(self, bus: EventBus):
        self.bus = bus

    async def start(self, run: RunState) -> None:
        run.status = RunStatus.AWAITING_APPROVAL
        run.log("Recommendation awaiting human approval", actor="workflow")
        await self._persist_decision(run)
        await self._publish(run, EventTypes.APPROVAL_NEEDED, {
            "decision": run.decision,
            "decision_record_id": run.decision_record_id,
        })

    async def resolve(self, run: RunState, approved: bool) -> None:
        if run.status != RunStatus.AWAITING_APPROVAL:
            return
        if not approved:
            run.status = RunStatus.REJECTED
            run.log("Recommendation rejected by operator", actor="workflow")
            await asyncio.to_thread(
                decision_memory.store_chain,
                incident=self._incident(run),
                decision=run.decision or {},
                workflow={"steps": []},
                outcome="rejected",
            )
            await self._update_persisted(run, approved=False)
            await self._publish(run, EventTypes.WORKFLOW_FINISHED, {"outcome": "rejected"})
            return

        run.status = RunStatus.EXECUTING_WORKFLOW
        await self._update_persisted(run, approved=True)
        await self._step(run, "notify", "Đã gửi thông báo tới các đơn vị liên quan")
        await self._step(run, "create_incident", f"Đã tạo sự cố cho mục tiêu: {run.goal}")
        await asyncio.to_thread(
            decision_memory.store_chain,
            incident=self._incident(run),
            decision=run.decision or {},
            workflow={"steps": [s["step"] for s in run.workflow_steps] + ["store_memory", "done"]},
            outcome="approved",
        )
        await self._step(run, "store_memory", "Đã lưu chuỗi Incident → Decision → Workflow → Outcome")
        await self._step(run, "done", "Workflow hoàn tất")
        run.status = RunStatus.DONE
        run.log("Workflow finished", actor="workflow")
        await self._publish(run, EventTypes.WORKFLOW_FINISHED, {"outcome": "approved"})
        await self._publish(run, EventTypes.RUN_FINISHED, {"status": run.status.value})

    def _incident(self, run: RunState) -> dict:
        return {
            "goal": run.goal,
            "district_id": run.district_id,
            "run_id": run.run_id,
            "risk": (run.decision or {}).get("risk"),
        }

    async def _step(self, run: RunState, step: str, detail: str) -> None:
        entry = {"step": step, "detail": detail, "ts": datetime.now(timezone.utc).isoformat()}
        run.workflow_steps.append(entry)
        run.log(f"Workflow step: {step}", actor="workflow")
        await self._publish(run, EventTypes.WORKFLOW_STEP, entry)

    async def _publish(self, run: RunState, event_type: str, payload: dict) -> None:
        await self.bus.publish(Event(type=event_type, payload=payload, run_id=run.run_id, source="workflow"))

    async def _persist_decision(self, run: RunState) -> None:
        try:
            from src.database.connection import AsyncSessionLocal
            from src.models.decision import AgentDecision
            d = run.decision or {}
            async with AsyncSessionLocal() as session:
                record = AgentDecision(
                    city_id="hanoi",
                    district_id=run.district_id,
                    query=run.goal,
                    prediction={"risk": d.get("risk"), "text": d.get("prediction")},
                    impact={},
                    recommendations=d.get("recommendation", []),
                    confidence=float(d.get("confidence", 0)),
                    explanation=[d.get("summary", "")],
                    evidence=d.get("evidence"),
                    requires_approval=True,
                    approved=None,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(record)
                await session.commit()
                await session.refresh(record)
                run.decision_record_id = record.id
        except Exception as e:
            logger.warning(f"Decision persistence skipped: {e}")

    async def _update_persisted(self, run: RunState, approved: bool) -> None:
        if run.decision_record_id is None:
            return
        try:
            from sqlalchemy import update

            from src.database.connection import AsyncSessionLocal
            from src.models.decision import AgentDecision
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(AgentDecision)
                    .where(AgentDecision.id == run.decision_record_id)
                    .values(approved=approved)
                )
                await session.commit()
        except Exception as e:
            logger.warning(f"Decision approval persistence skipped: {e}")
