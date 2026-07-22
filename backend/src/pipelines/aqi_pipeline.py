import asyncio
import random
from datetime import datetime, timezone
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.aqi import AQI
from src.repositories.district_repo import DistrictRepo
from src.repositories.aqi_repo import AQIRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)

OPENAQ_URL = (
    "https://api.openaq.org/v3/locations"
    "?coordinates=21.0285,105.8542&radius=50000&limit=10"
)

HTTP_TIMEOUT_SECONDS = 10


class AQIPipeline:
    @staticmethod
    async def run(session: AsyncSession) -> None:
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as http:
                async with http.get(OPENAQ_URL) as resp:
                    data = await resp.json()
        except asyncio.TimeoutError:
            logger.warning(f"OpenAQ call timed out after {HTTP_TIMEOUT_SECONDS}s")
            return
        except aiohttp.ContentTypeError as e:
            logger.warning(f"OpenAQ returned a non-JSON response: {e}")
            return
        except Exception as e:
            logger.warning(f"OpenAQ call failed: {e}")
            return

        timestamp = datetime.now(timezone.utc)
        districts = await DistrictRepo.get_all(session)

        aqis = [
            AQI(
                city_id=district.city_id,
                district_id=district.id,
                timestamp=timestamp,
                pm25=random.uniform(15, 120),
                pm10=random.uniform(20, 150),
                co=random.uniform(0.1, 2.0),
                no2=random.uniform(10, 80),
                aqi_index=random.randint(50, 180),
            )
            for district in districts
        ]
        await AQIRepo.save_all(session, aqis)
        logger.info(f"Saved AQI for {len(districts)} districts")
