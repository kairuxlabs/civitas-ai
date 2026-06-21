import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.database.connection import AsyncSessionLocal
from src.pipelines.weather_pipeline import WeatherPipeline
from src.pipelines.aqi_pipeline import AQIPipeline
from src.pipelines.feedback_pipeline import FeedbackPipeline
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def run_weather():
    async with AsyncSessionLocal() as session:
        await WeatherPipeline.run(session)

async def run_aqi():
    async with AsyncSessionLocal() as session:
        await AQIPipeline.run(session)

async def run_feedback():
    async with AsyncSessionLocal() as session:
        await FeedbackPipeline.run(session)

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_weather, "interval", minutes=15, id="weather")
    scheduler.add_job(run_aqi, "interval", minutes=60, id="aqi")
    scheduler.add_job(run_feedback, "interval", minutes=30, id="feedback")

    # Run all pipelines immediately on startup
    scheduler.start()
    await run_weather()
    await run_aqi()
    await run_feedback()

    logger.info("Scheduler started")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
