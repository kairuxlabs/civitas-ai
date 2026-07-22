import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.api.routes import districts, scores, chat, simulator, timeline, aqi
from src.api.routes import decisions
from src.api.routes import runtime as runtime_routes
from src.api.routes import simulation_v2
from src.api.routes import decision_sessions
from src.api.routes import system
from src.api.routes import knowledge
from src.api.routes.ws import router as ws_router
from src.database.connection import Base, engine, AsyncSessionLocal
import src.models.district  # noqa: F401
import src.models.weather   # noqa: F401
import src.models.aqi       # noqa: F401
import src.models.city_score # noqa: F401
import src.models.decision  # noqa: F401
import src.models.event     # noqa: F401
import src.models.feedback  # noqa: F401
import src.models.decision_session  # noqa: F401
from src.utils.config import settings
from src.scheduler.main import run_all
from src.scheduler.registry import scheduler
from src.knowledge_pipeline import scheduler as knowledge_scheduler
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def _ensure_hot_path_indexes():
    """create_all() only creates missing tables — it never retroactively adds
    indexes/columns to tables that already exist (e.g. the already-deployed
    Render Postgres database). Weather/AQI didn't have composite indexes when
    they were first deployed, so add them here idempotently on every startup.
    CREATE INDEX IF NOT EXISTS works on both Postgres and SQLite (the test
    suite's dialect). The whole operation (including transaction commit) is
    wrapped so a failure here — e.g. a poisoned Postgres transaction — never
    blocks app startup."""
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_weather_district_ts ON weather (district_id, timestamp)")
            )
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_aqi_district_ts ON aqi (district_id, timestamp)")
            )
    except Exception as e:
        logger.warning(f"Failed to ensure hot-path indexes, continuing startup: {e}")


async def _seed_districts(session):
    from src.models.district import District
    from sqlalchemy import select
    result = await session.execute(select(District).limit(1))
    if result.scalar_one_or_none() is not None:
        return
    hanoi_districts = [
        "Hoàn Kiếm", "Ba Đình", "Đống Đa", "Hai Bà Trưng", "Hoàng Mai",
        "Thanh Xuân", "Cầu Giấy", "Long Biên", "Nam Từ Liêm",
        "Bắc Từ Liêm", "Tây Hồ", "Hà Đông",
    ]
    for name in hanoi_districts:
        session.add(District(city_id="hanoi", name=name))
    await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tự động tạo các bảng và seed dữ liệu quận huyện
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Separate transaction from create_all so an index failure can't abort
    # the table-creation commit (relevant on Postgres, where an error inside
    # a transaction poisons it until rollback).
    await _ensure_hot_path_indexes()

    async with AsyncSessionLocal() as session:
        await _seed_districts(session)

    # Khởi chạy Scheduler ngay trong tiến trình FastAPI
    scheduler.add_job(run_all, "interval", minutes=15, id="full_pipeline")
    knowledge_scheduler.register(scheduler)
    scheduler.start()
    
    # Kích hoạt chạy lượt đầu tiên bất đồng bộ dưới background để dashboard có dữ liệu ngay
    asyncio.create_task(run_all())
    
    yield
    scheduler.shutdown()


app = FastAPI(title="CityOS API", version="2.0.0", lifespan=lifespan)

_cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)
app.include_router(districts.router)
app.include_router(scores.router)
app.include_router(chat.router)
app.include_router(simulator.router)
app.include_router(timeline.router)
app.include_router(aqi.router)
app.include_router(decisions.router)
app.include_router(runtime_routes.router)
app.include_router(simulation_v2.router)
app.include_router(decision_sessions.router)
app.include_router(system.router)
app.include_router(knowledge.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
