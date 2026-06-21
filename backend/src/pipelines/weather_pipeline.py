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


class WeatherPipeline:
    @staticmethod
    async def run(session: AsyncSession) -> None:
        async with aiohttp.ClientSession() as http:
            async with http.get(OPEN_METEO_URL) as resp:
                data = await resp.json()

        current = data.get("current", {})
        timestamp = datetime.now(timezone.utc)

        districts = await DistrictRepo.get_all(session)
        for district in districts:
            weather = Weather(
                city_id=district.city_id,
                district_id=district.id,
                timestamp=timestamp,
                temperature=current.get("temperature_2m"),
                humidity=current.get("relative_humidity_2m"),
                rain=current.get("precipitation"),
                wind_speed=current.get("wind_speed_10m"),
            )
            await WeatherRepo.save(session, weather)
            logger.info(f"Saved weather for district {district.name}")
