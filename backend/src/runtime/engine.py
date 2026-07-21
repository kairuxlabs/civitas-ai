# backend/src/runtime/engine.py
"""Runtime engine: wires Planner → Scheduler → Reflection → Decision → Workflow
over one EventBus and bridges every runtime event to the WebSocket manager.
"""
import asyncio

from src.runtime.decision import make_decision
from src.runtime.event_bus import Event, EventBus, EventTypes
from src.runtime.planner import create_plan
from src.runtime.reflection import Reflection
from src.runtime.scheduler import Scheduler
from src.runtime.state import RunState, RunStatus, run_store
from src.runtime.workers import WORKERS
from src.runtime.workflow import WorkflowRuntime
from src.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_CONTEXT = {
    "city_id": "hanoi",
    "weather_data": {"temperature": 30, "humidity": 70, "rain": 0, "wind_speed": 10},
    "aqi_data": {"pm25": 50, "pm10": 80, "co": 1.0, "no2": 40, "aqi_index": 100},
    "event_data": [],
    "feedback_data": [],
}


class RuntimeEngine:
    def __init__(self, broadcast_ws: bool = True):
        self.bus = EventBus()
        self.scheduler = Scheduler(self.bus)
        self.reflection = Reflection(self.bus)
        self.workflow = WorkflowRuntime(self.bus)
        self._exec_tasks: dict[str, asyncio.Task] = {}
        if broadcast_ws:
            self.bus.subscribe("*", self._bridge_to_websocket)

    async def _bridge_to_websocket(self, event: Event) -> None:
        from src.ws.manager import manager
        await manager.broadcast({
            "type": "runtime_event",
            "event": event.type,
            "run_id": event.run_id,
            "payload": event.payload,
            "source": event.source,
            "ts": event.ts,
        })

    async def submit_goal(
        self,
        goal: str,
        district_id: int = 1,
        context_overrides: dict | None = None,
    ) -> RunState:
        run = RunState(goal=goal, district_id=district_id)
        run.context = {
            **{k: (dict(v) if isinstance(v, dict) else list(v)) for k, v in _DEFAULT_CONTEXT.items()},
            "query": goal,
            "district_id": district_id,
            **(context_overrides or {}),
        }
        run_store.add(run)
        run.log(f"Goal received: {goal}", actor="user")
        await self._create_decision_session(run)
        await self.bus.publish(Event(
            type=EventTypes.GOAL_RECEIVED, payload={"goal": goal, "district_id": district_id},
            run_id=run.run_id, source="api",
        ))
        self._exec_tasks[run.run_id] = asyncio.create_task(self._execute(run))
        return run

    async def wait_for(self, run_id: str) -> None:
        """Await run execution (used by tests and synchronous callers)."""
        task = self._exec_tasks.get(run_id)
        if task:
            await task

    async def _execute(self, run: RunState) -> None:
        try:
            specs = await create_plan(run.goal)
            run.add_tasks(specs)
            run.log(f"Plan created with {len(specs)} tasks", actor="planner")
            await self.bus.publish(Event(
                type=EventTypes.PLAN_CREATED,
                payload={"tasks": [{"id": s.id, "agent": s.agent, "depends_on": s.depends_on} for s in specs]},
                run_id=run.run_id, source="planner",
            ))
            await self._mark_session_analyzing(run)

            run.status = RunStatus.RUNNING
            await self.scheduler.execute(run, WORKERS)

            run.status = RunStatus.REFLECTING
            followups = await self.reflection.review(run)
            if followups:
                run.add_tasks(followups)
                await self.scheduler.execute(run, WORKERS)

            run.status = RunStatus.DECIDING
            run.decision = await make_decision(run, self.bus)
            await self._mark_session_recommend(run)

            await self.workflow.start(run)
        except Exception as e:
            logger.exception(f"Run {run.run_id} failed")
            run.status = RunStatus.FAILED
            run.log(f"Run failed: {e}", actor="runtime")
            await self.bus.publish(Event(
                type=EventTypes.RUN_FINISHED, payload={"status": "failed", "error": str(e)},
                run_id=run.run_id, source="runtime",
            ))

    async def resolve(self, run_id: str, approved: bool) -> RunState | None:
        run = run_store.get(run_id)
        if run is None:
            return None
        await self.workflow.resolve(run, approved)
        return run

    async def _create_decision_session(self, run: RunState) -> None:
        try:
            from src.database.connection import AsyncSessionLocal
            from src.services.decision_session_service import DecisionSessionService
            async with AsyncSessionLocal() as session:
                await DecisionSessionService.create(
                    session, run_id=run.run_id, goal=run.goal, district_id=run.district_id,
                )
        except Exception as e:
            logger.warning(f"DecisionSession create skipped for {run.run_id}: {e}")

    async def _mark_session_analyzing(self, run: RunState) -> None:
        try:
            from src.database.connection import AsyncSessionLocal
            from src.services.decision_session_service import DecisionSessionService
            async with AsyncSessionLocal() as session:
                await DecisionSessionService.mark_analyzing(session, run_id=run.run_id)
        except Exception as e:
            logger.warning(f"DecisionSession mark_analyzing skipped for {run.run_id}: {e}")

    async def _mark_session_recommend(self, run: RunState) -> None:
        try:
            from src.database.connection import AsyncSessionLocal
            from src.services.decision_session_service import DecisionSessionService
            async with AsyncSessionLocal() as session:
                await DecisionSessionService.mark_recommend(session, run_id=run.run_id)
        except Exception as e:
            logger.warning(f"DecisionSession mark_recommend skipped for {run.run_id}: {e}")


engine = RuntimeEngine()
