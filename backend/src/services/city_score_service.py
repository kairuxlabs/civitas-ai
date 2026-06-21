from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.city_score import CityScore
from src.repositories.weather_repo import WeatherRepo
from src.repositories.aqi_repo import AQIRepo
from src.repositories.city_score_repo import CityScoreRepo


class CityScoreService:
    @staticmethod
    async def calculate_and_save(session: AsyncSession, district_id: int) -> CityScore:
        weather = await WeatherRepo.get_latest(session, district_id)
        aqi = await AQIRepo.get_latest(session, district_id)

        aqi_index = aqi.aqi_index if aqi and aqi.aqi_index else 100
        pm25 = aqi.pm25 if aqi and aqi.pm25 else 50
        rain = weather.rain if weather and weather.rain else 0

        traffic_score = max(0, min(100, 100 - (aqi_index / 3)))
        environment_score = max(0, min(100, 100 - (pm25 / 1.5)))
        citizen_score = 70.0  # placeholder until feedback aggregation
        risk_score = min(100, (rain * 5) + (aqi_index / 4))
        overall_score = (traffic_score + environment_score + citizen_score + (100 - risk_score)) / 4

        score = CityScore(
            city_id="hanoi",
            district_id=district_id,
            timestamp=datetime.now(timezone.utc),
            traffic_score=round(traffic_score, 1),
            environment_score=round(environment_score, 1),
            citizen_score=round(citizen_score, 1),
            risk_score=round(risk_score, 1),
            overall_score=round(overall_score, 1),
        )
        return await CityScoreRepo.save(session, score)
