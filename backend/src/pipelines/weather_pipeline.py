import asyncio
from datetime import datetime, timezone
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.weather import Weather
from src.pipelines.district_coordinates import coordinates_for
from src.repositories.district_repo import DistrictRepo
from src.repositories.weather_repo import WeatherRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)

OPEN_METEO_BASE_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
)

HTTP_TIMEOUT_SECONDS = 10


class WeatherPipeline:
    @staticmethod
    async def run(session: AsyncSession) -> int:
        """Returns the number of district rows saved (0 on any graceful
        skip/failure) so callers — the 15-min scheduler and the on-demand
        crawl endpoint alike — can report a truthful count instead of a
        bare 'ok'."""
        districts = await DistrictRepo.get_all(session)
        if not districts:
            logger.info("No districts seeded — skipping weather crawl")
            return 0

        coords = [coordinates_for(district.name) for district in districts]
        lats = ",".join(str(lat) for lat, _ in coords)
        lons = ",".join(str(lon) for _, lon in coords)
        url = f"{OPEN_METEO_BASE_URL}&latitude={lats}&longitude={lons}"

        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as http:
                async with http.get(url) as resp:
                    data = await resp.json()
        except asyncio.TimeoutError:
            logger.warning(f"Open-Meteo call timed out after {HTTP_TIMEOUT_SECONDS}s")
            return 0
        except aiohttp.ContentTypeError as e:
            logger.warning(f"Open-Meteo returned a non-JSON response: {e}")
            return 0
        except Exception as e:
            logger.warning(f"Open-Meteo call failed: {e}")
            return 0

        # Open-Meteo returns a bare object for one coordinate pair, and a list
        # of the same structure (one per input pair, same order) once more
        # than one lat/lon is requested — normalize to a list either way.
        per_location = data if isinstance(data, list) else [data]

        timestamp = datetime.now(timezone.utc)
        weathers = []
        for index, district in enumerate(districts):
            current = per_location[index].get("current", {}) if index < len(per_location) else {}
            weathers.append(Weather(
                city_id=district.city_id,
                district_id=district.id,
                timestamp=timestamp,
                temperature=current.get("temperature_2m"),
                humidity=current.get("relative_humidity_2m"),
                rain=current.get("precipitation"),
                wind_speed=current.get("wind_speed_10m"),
            ))
        await WeatherRepo.save_all(session, weathers)
        logger.info(f"Saved per-district weather for {len(districts)} districts")
        return len(weathers)
