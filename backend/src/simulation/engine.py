# backend/src/simulation/engine.py
"""Digital Twin simulation engine (spec_v2 §12).

Generates synthetic city data on a background loop: weather + AQI rows for
every district, citizen feedback and occasional events, all drifting toward
the active scenario profile. When thresholds are crossed it can autonomously
submit a goal to the v2 runtime ("Agent tự chạy").

All side effects (DB, WebSocket, runtime engine) are injectable and
best-effort: the engine keeps ticking without any of them.
"""
import asyncio
import random
import time
from datetime import datetime, timezone

from src.simulation.profiles import PROFILES, ScenarioProfile
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SimulationEngine:
    def __init__(self, submit_goal=None, broadcast=None, persist: bool = True):
        self._submit_goal = submit_goal
        self._broadcast = broadcast
        self._persist_enabled = persist
        self._task: asyncio.Task | None = None

        self.scenario: str = "normal"
        self.interval_s: float = 30.0
        self.auto_goal: bool = True
        self.district_id: int = 1
        self.auto_goal_cooldown_s: float = 300.0
        self.running: bool = False
        self.tick_count: int = 0
        self.last_auto_goal_ts: float | None = None
        self.last_auto_goal_run: str | None = None
        self.values: dict = {"rain": 0.0, "aqi": 90.0, "temperature": 30.0, "humidity": 70.0, "wind_speed": 10.0}

    # ── lifecycle ────────────────────────────────────────────────────────

    async def start(
        self, scenario: str, interval_s: float = 30.0, auto_goal: bool = True, district_id: int = 1
    ) -> dict:
        if scenario not in PROFILES:
            raise ValueError(f"Unknown scenario '{scenario}'. Available: {sorted(PROFILES)}")
        await self.stop()
        self.scenario = scenario
        self.interval_s = float(interval_s)  # minimum enforced at the API layer
        self.auto_goal = auto_goal
        self.district_id = district_id
        self.last_auto_goal_ts = None
        self.last_auto_goal_run = None
        self.running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"Simulation started: {scenario} every {self.interval_s}s (auto_goal={auto_goal})")
        return self.status()

    async def stop(self) -> dict:
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        return self.status()

    def status(self) -> dict:
        return {
            "running": self.running,
            "scenario": self.scenario,
            "scenario_label": PROFILES[self.scenario].label,
            "interval_s": self.interval_s,
            "auto_goal": self.auto_goal,
            "district_id": self.district_id,
            "tick": self.tick_count,
            "values": {k: round(v, 1) for k, v in self.values.items()},
            "last_auto_goal": self.last_auto_goal_run,
        }

    async def _loop(self) -> None:
        while self.running:
            try:
                await self.tick()
            except Exception as e:
                logger.warning(f"Simulation tick failed: {e}")
            await asyncio.sleep(self.interval_s)

    # ── data generation ──────────────────────────────────────────────────

    def _drift(self, current: float, target_range: tuple[float, float], noise: float) -> float:
        target = (target_range[0] + target_range[1]) / 2
        value = current + (target - current) * 0.35 + random.uniform(-noise, noise)
        return max(0.0, value)

    def _next_values(self, profile: ScenarioProfile) -> dict:
        v = self.values
        return {
            "rain": self._drift(v["rain"], profile.rain_range, noise=2.0),
            "aqi": min(300.0, self._drift(v["aqi"], profile.aqi_range, noise=8.0)),
            "temperature": self._drift(v["temperature"], profile.temp_range, noise=0.6),
            "humidity": max(20.0, min(100.0, v["humidity"] + random.uniform(-4, 4) + (8 if profile.rain_range[1] > 20 else 0) * 0.2)),
            "wind_speed": max(0.0, v["wind_speed"] + random.uniform(-2, 2)),
        }

    async def tick(self) -> dict:
        profile = PROFILES[self.scenario]
        self.values = self._next_values(profile)
        self.tick_count += 1

        if self._persist_enabled:
            try:
                await self._persist(profile)
            except Exception as e:
                logger.warning(f"Simulation persistence skipped: {e}")

        snapshot = {
            "type": "simulation_tick",
            "scenario": self.scenario,
            "tick": self.tick_count,
            "rain": round(self.values["rain"], 1),
            "aqi": round(self.values["aqi"], 1),
            "temperature": round(self.values["temperature"], 1),
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        await self._send_ws(snapshot)
        await self._maybe_auto_goal()
        return snapshot

    async def _persist(self, profile: ScenarioProfile) -> None:
        from src.database.connection import AsyncSessionLocal
        from src.models.aqi import AQI
        from src.models.event import Event
        from src.models.feedback import CitizenFeedback
        from src.models.weather import Weather
        from src.repositories.district_repo import DistrictRepo

        now = datetime.now(timezone.utc)
        v = self.values
        async with AsyncSessionLocal() as session:
            districts = await DistrictRepo.get_all(session)
            for d in districts:
                jitter = random.uniform(0.85, 1.15)
                session.add(Weather(
                    city_id=d.city_id, district_id=d.id, timestamp=now,
                    temperature=round(v["temperature"] * random.uniform(0.97, 1.03), 1),
                    humidity=round(v["humidity"], 1),
                    rain=round(v["rain"] * jitter, 1),
                    wind_speed=round(v["wind_speed"], 1),
                ))
                aqi_val = min(300.0, v["aqi"] * jitter)
                session.add(AQI(
                    city_id=d.city_id, district_id=d.id, timestamp=now,
                    pm25=round(aqi_val * 0.6, 1), pm10=round(aqi_val * 0.9, 1),
                    co=round(random.uniform(0.5, 2.0), 2), no2=round(aqi_val * 0.3, 1),
                    aqi_index=int(round(aqi_val)),  # column is Integer
                ))
            if profile.feedback_pool and districts:
                for _ in range(random.randint(1, 3)):
                    category, sentiment, content = random.choice(profile.feedback_pool)
                    if random.random() > profile.negative_feedback_ratio and sentiment == "negative":
                        continue
                    d = random.choice(districts)
                    session.add(CitizenFeedback(
                        city_id=d.city_id, district_id=d.id,
                        category=category, sentiment=sentiment,
                        content=f"{content} (mô phỏng)", created_at=now,
                    ))
            if profile.event_templates and districts and random.random() < profile.event_chance:
                title, category, impact = random.choice(profile.event_templates)
                d = random.choice(districts)
                session.add(Event(
                    city_id=d.city_id, district_id=d.id,
                    title=f"{title} (mô phỏng)", category=category,
                    start_time=now, impact_level=impact,
                ))
            await session.commit()

    # ── autonomous trigger ───────────────────────────────────────────────

    async def _maybe_auto_goal(self) -> None:
        if not self.auto_goal:
            return
        profile = PROFILES[self.scenario]
        if profile.goal_trigger is None or profile.goal_text is None:
            return
        if not profile.goal_trigger(self.values, profile):
            return
        now = time.monotonic()
        if self.last_auto_goal_ts and now - self.last_auto_goal_ts < self.auto_goal_cooldown_s:
            return
        self.last_auto_goal_ts = now

        goal = profile.goal_text(self.values)
        rain, aqi = self.values["rain"], self.values["aqi"]

        overrides = {
            "weather_data": {
                "temperature": round(self.values["temperature"], 1),
                "humidity": round(self.values["humidity"], 1),
                "rain": round(rain, 1),
                "wind_speed": round(self.values["wind_speed"], 1),
            },
            "aqi_data": {
                "pm25": round(aqi * 0.6, 1), "pm10": round(aqi * 0.9, 1),
                "co": 1.0, "no2": round(aqi * 0.3, 1), "aqi_index": round(aqi, 1),
            },
        }
        try:
            submit = self._submit_goal or self._default_submit_goal
            run = await submit(goal, district_id=self.district_id, context_overrides=overrides)
            self.last_auto_goal_run = getattr(run, "run_id", None) or goal
            logger.info(f"Simulation auto-submitted goal: {goal}")
        except Exception as e:
            logger.warning(f"Auto-goal submission failed: {e}")

    @staticmethod
    async def _default_submit_goal(goal: str, district_id: int, context_overrides: dict):
        from src.runtime.engine import engine
        return await engine.submit_goal(goal, district_id=district_id, context_overrides=context_overrides)

    async def _send_ws(self, data: dict) -> None:
        try:
            if self._broadcast is not None:
                await self._broadcast(data)
            else:
                from src.ws.manager import manager
                await manager.broadcast(data)
        except Exception as e:
            logger.warning(f"Simulation broadcast failed: {e}")


simulation = SimulationEngine()
