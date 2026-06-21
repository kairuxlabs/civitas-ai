import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.database.connection import AsyncSessionLocal
from src.pipelines.weather_pipeline import WeatherPipeline
from src.pipelines.aqi_pipeline import AQIPipeline
from src.pipelines.feedback_pipeline import FeedbackPipeline
from src.services.city_score_service import CityScoreService
from src.repositories.district_repo import DistrictRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def run_all():
    async with AsyncSessionLocal() as session:
        await WeatherPipeline.run(session)
        await AQIPipeline.run(session)
        await FeedbackPipeline.run(session)
        districts = await DistrictRepo.get_all(session)
        for d in districts:
            await CityScoreService.calculate_and_save(session, d.id)
        logger.info(f"Full pipeline run complete for {len(districts)} districts")

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_all, "interval", minutes=15, id="full_pipeline")
    scheduler.start()
    await run_all()
    logger.info("Scheduler started — running every 15 minutes")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
