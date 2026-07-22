import asyncio
from datetime import datetime, timezone
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.weather import Weather
from src.repositories.district_repo import DistrictRepo
from src.repositories.weather_repo import WeatherRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=21.0285&longitude=105.8542"
    "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
)

HTTP_TIMEOUT_SECONDS = 10


class WeatherPipeline:
    @staticmethod
    async def run(session: AsyncSession) -> None:
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as http:
                async with http.get(OPEN_METEO_URL) as resp:
                    data = await resp.json()
        except asyncio.TimeoutError:
            logger.warning(f"Open-Meteo call timed out after {HTTP_TIMEOUT_SECONDS}s")
            return
        except aiohttp.ContentTypeError as e:
            logger.warning(f"Open-Meteo returned a non-JSON response: {e}")
            return
        except Exception as e:
            logger.warning(f"Open-Meteo call failed: {e}")
            return

        current = data.get("current", {})
        timestamp = datetime.now(timezone.utc)

        districts = await DistrictRepo.get_all(session)
        weathers = [
            Weather(
                city_id=district.city_id,
                district_id=district.id,
                timestamp=timestamp,
                temperature=current.get("temperature_2m"),
                humidity=current.get("relative_humidity_2m"),
                rain=current.get("precipitation"),
                wind_speed=current.get("wind_speed_10m"),
            )
            for district in districts
        ]
        await WeatherRepo.save_all(session, weathers)
        logger.info(f"Saved weather for {len(districts)} districts")
