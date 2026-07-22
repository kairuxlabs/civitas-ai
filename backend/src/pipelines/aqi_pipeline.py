import asyncio
from datetime import datetime, timezone
from math import atan2, cos, radians, sin, sqrt

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.aqi import AQI
from src.pipelines.district_coordinates import coordinates_for
from src.repositories.district_repo import DistrictRepo
from src.repositories.aqi_repo import AQIRepo
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

OPENAQ_LOCATIONS_URL = (
    "https://api.openaq.org/v3/locations"
    "?coordinates=21.0285,105.8542&radius=50000&limit=10"
)
OPENAQ_LATEST_URL_TEMPLATE = "https://api.openaq.org/v3/locations/{id}/latest"

HTTP_TIMEOUT_SECONDS = 10

# US EPA PM2.5 24h breakpoints (µg/m³) -> AQI, used to derive aqi_index from
# a real measured pm25 reading instead of a random placeholder.
_PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 350.4, 301, 400),
    (350.5, 500.4, 401, 500),
]

# OpenAQ sensor parameter names we care about, mapped to the AQI model field
# they populate.
_TRACKED_PARAMETERS = {"pm25", "pm10", "co", "no2"}


def pm25_to_aqi(pm25: float) -> int:
    """US EPA linear-interpolation breakpoint formula."""
    clamped = max(0.0, min(pm25, _PM25_BREAKPOINTS[-1][1]))
    for lo_conc, hi_conc, lo_idx, hi_idx in _PM25_BREAKPOINTS:
        if lo_conc <= clamped <= hi_conc:
            return round((hi_idx - lo_idx) / (hi_conc - lo_conc) * (clamped - lo_conc) + lo_idx)
    return _PM25_BREAKPOINTS[-1][3]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r_km = 6371.0
    p1, p2 = radians(lat1), radians(lat2)
    d_phi = radians(lat2 - lat1)
    d_lambda = radians(lon2 - lon1)
    a = sin(d_phi / 2) ** 2 + cos(p1) * cos(p2) * sin(d_lambda / 2) ** 2
    return 2 * r_km * atan2(sqrt(a), sqrt(1 - a))


def _parse_stations(data: dict) -> list[dict]:
    """Extract {id, lat, lon, sensors: {parameter_name: sensor_id}} per
    OpenAQ location, keeping only stations that expose a tracked parameter."""
    stations = []
    for location in data.get("results") or []:
        coords = location.get("coordinates") or {}
        lat, lon = coords.get("latitude"), coords.get("longitude")
        if lat is None or lon is None:
            continue
        sensors = {
            sensor["parameter"]["name"]: sensor["id"]
            for sensor in location.get("sensors") or []
            if sensor.get("parameter", {}).get("name") in _TRACKED_PARAMETERS
        }
        if not sensors:
            continue
        stations.append({"id": location["id"], "lat": lat, "lon": lon, "sensors": sensors})
    return stations


async def _fetch_latest_reading(http: aiohttp.ClientSession, station: dict) -> dict | None:
    """One station's latest measurement per tracked parameter, or None if
    the call fails or returns nothing usable — a single dead station must
    not take down the whole crawl."""
    try:
        async with http.get(OPENAQ_LATEST_URL_TEMPLATE.format(id=station["id"])) as resp:
            payload = await resp.json()
    except Exception as e:
        logger.warning(f"OpenAQ latest lookup failed for station {station['id']}: {e}")
        return None

    sensor_id_to_param = {sensor_id: name for name, sensor_id in station["sensors"].items()}
    values: dict[str, float] = {}
    for result in payload.get("results") or []:
        param = sensor_id_to_param.get(result.get("sensorsId"))
        if param and result.get("value") is not None:
            values[param] = result["value"]

    if "pm25" not in values:
        return None
    return {"lat": station["lat"], "lon": station["lon"], **values}


class AQIPipeline:
    @staticmethod
    async def run(session: AsyncSession) -> int:
        """Returns the number of district rows saved (0 on any graceful
        skip/failure) so callers — the 15-min scheduler and the on-demand
        crawl endpoint alike — can report a truthful count instead of a
        bare 'ok'."""
        if not settings.openaq_api_key:
            logger.info("OPENAQ_API_KEY not configured — skipping AQI crawl (no fabricated data)")
            return 0

        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
        headers = {"X-API-Key": settings.openaq_api_key}
        try:
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as http:
                async with http.get(OPENAQ_LOCATIONS_URL) as resp:
                    data = await resp.json()

                stations = _parse_stations(data)
                if not stations:
                    logger.warning("OpenAQ returned no stations with usable sensors near Hanoi")
                    return 0

                readings = await asyncio.gather(*(_fetch_latest_reading(http, s) for s in stations))
        except asyncio.TimeoutError:
            logger.warning(f"OpenAQ call timed out after {HTTP_TIMEOUT_SECONDS}s")
            return 0
        except aiohttp.ContentTypeError as e:
            logger.warning(f"OpenAQ returned a non-JSON response: {e}")
            return 0
        except Exception as e:
            logger.warning(f"OpenAQ call failed: {e}")
            return 0

        usable = [r for r in readings if r is not None]
        if not usable:
            logger.warning("OpenAQ latest lookups returned no usable PM2.5 readings")
            return 0

        timestamp = datetime.now(timezone.utc)
        districts = await DistrictRepo.get_all(session)
        aqis = []
        for district in districts:
            lat, lon = coordinates_for(district.name)
            nearest = min(usable, key=lambda r: _haversine_km(lat, lon, r["lat"], r["lon"]))
            pm25 = nearest["pm25"]
            aqis.append(AQI(
                city_id=district.city_id,
                district_id=district.id,
                timestamp=timestamp,
                pm25=pm25,
                pm10=nearest.get("pm10"),
                co=nearest.get("co"),
                no2=nearest.get("no2"),
                aqi_index=pm25_to_aqi(pm25),
            ))
        await AQIRepo.save_all(session, aqis)
        logger.info(f"Saved AQI for {len(districts)} districts from {len(usable)} live OpenAQ station(s)")
        return len(aqis)
