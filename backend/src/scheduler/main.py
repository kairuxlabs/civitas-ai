import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.database.connection import AsyncSessionLocal
from src.pipelines.weather_pipeline import WeatherPipeline
from src.pipelines.aqi_pipeline import AQIPipeline
from src.pipelines.feedback_pipeline import FeedbackPipeline
from src.services.city_score_service import CityScoreService
from src.repositories.district_repo import DistrictRepo
from src.knowledge_pipeline import scheduler as knowledge_scheduler
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def run_all():
    async with AsyncSessionLocal() as session:
        try:
            await WeatherPipeline.run(session)
        except Exception as e:
            logger.warning(f"WeatherPipeline step failed, continuing: {e}")
        try:
            await AQIPipeline.run(session)
        except Exception as e:
            logger.warning(f"AQIPipeline step failed, continuing: {e}")
        try:
            await FeedbackPipeline.run(session)
        except Exception as e:
            logger.warning(f"FeedbackPipeline step failed, continuing: {e}")

        districts = await DistrictRepo.get_all(session)
        for d in districts:
            try:
                await CityScoreService.calculate_and_save(session, d.id)
            except Exception as e:
                logger.warning(f"CityScoreService failed for district {d.id}, continuing: {e}")
        logger.info(f"Full pipeline run complete for {len(districts)} districts")

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_all, "interval", minutes=15, id="full_pipeline")
    knowledge_scheduler.register(scheduler)
    scheduler.start()
    try:
        await run_all()
    except Exception as e:
        logger.error(f"Initial run_all() failed on startup, continuing to idle loop: {e}")
    logger.info("Scheduler started — running every 15 minutes")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
