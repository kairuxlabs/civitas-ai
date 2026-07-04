import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.api.routes import districts, scores, chat, simulator, timeline, aqi
from src.api.routes import decisions
from src.api.routes import runtime as runtime_routes
from src.api.routes.ws import router as ws_router
from src.database.connection import Base, engine, AsyncSessionLocal
import src.models.district  # noqa: F401
import src.models.weather   # noqa: F401
import src.models.aqi       # noqa: F401
import src.models.city_score # noqa: F401
import src.models.decision  # noqa: F401
import src.models.event     # noqa: F401
import src.models.feedback  # noqa: F401
from src.utils.config import settings
from src.scheduler.main import run_all


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
    
    async with AsyncSessionLocal() as session:
        await _seed_districts(session)
    
    # Khởi chạy Scheduler ngay trong tiến trình FastAPI
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_all, "interval", minutes=15, id="full_pipeline")
    scheduler.start()
    
    # Kích hoạt chạy lượt đầu tiên bất đồng bộ dưới background để dashboard có dữ liệu ngay
    asyncio.create_task(run_all())
    
    yield
    scheduler.shutdown()


app = FastAPI(title="CityOS API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
