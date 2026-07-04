"""
Seed demo data for all 12 Hanoi districts.
Run: python -m scripts.seed_demo  (from backend/)
"""
import asyncio
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from src.database.connection import engine, AsyncSessionLocal, Base
from src.models.district import District
from src.models.weather import Weather
from src.models.aqi import AQI
from src.models.event import Event
from src.models.feedback import CitizenFeedback
from src.services.city_score_service import CityScoreService

DISTRICTS = [
    'Hoàn Kiếm', 'Ba Đình', 'Đống Đa', 'Hai Bà Trưng',
    'Hoàng Mai', 'Thanh Xuân', 'Cầu Giấy', 'Long Biên',
    'Nam Từ Liêm', 'Bắc Từ Liêm', 'Tây Hồ', 'Hà Đông',
]

EVENTS_DATA = [
    {'title': 'Lễ hội ẩm thực Hà Nội 2024', 'category': 'festival', 'impact': 'medium'},
    {'title': 'Marathon Hà Nội', 'category': 'sport', 'impact': 'high'},
    {'title': 'Hội nghị ASEAN', 'category': 'conference', 'impact': 'high'},
    {'title': 'Triển lãm ô tô', 'category': 'exhibition', 'impact': 'medium'},
    {'title': 'Thi đấu bóng đá quốc tế', 'category': 'sport', 'impact': 'high'},
]

FEEDBACK_TEMPLATES = [
    ('traffic', 'negative', 'Kẹt xe kinh khủng ở đường Nguyễn Trãi, mất 45 phút mới qua được.'),
    ('traffic', 'negative', 'Giờ cao điểm đường tắc từ đầu đến cuối, cần thêm đèn tín hiệu.'),
    ('environment', 'negative', 'Không khí hôm nay ngột ngạt, mùi khói xe rất nặng.'),
    ('environment', 'positive', 'Công viên Thống Nhất sạch sẽ, không khí trong lành buổi sáng.'),
    ('infrastructure', 'negative', 'Đường Trần Duy Hưng xuất hiện ổ gà lớn gây nguy hiểm.'),
    ('infrastructure', 'positive', 'Hệ thống đèn đường khu vực Cầu Giấy được sửa, sáng hơn nhiều.'),
    ('public_service', 'positive', 'Xe buýt tuyến 32 đúng giờ, sạch sẽ, nhân viên thân thiện.'),
    ('safety', 'negative', 'Đêm qua có vụ trộm xe máy trên phố Hàng Bông.'),
]


async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # ── Districts ──────────────────────────────────────────────────────────
        existing = await session.execute(select(District))
        existing_names = {d.name for d in existing.scalars().all()}

        district_objs = []
        for name in DISTRICTS:
            if name not in existing_names:
                d = District(city_id='hanoi', name=name)
                session.add(d)
                await session.flush()
            else:
                r = await session.execute(select(District).where(District.name == name))
                d = r.scalar_one()
            district_objs.append(d)
        await session.flush()

        now = datetime.now(timezone.utc)

        # ── Weather & AQI — 24h history per district ───────────────────────────
        for d in district_objs:
            for hours_ago in range(23, -1, -1):
                ts = now - timedelta(hours=hours_ago)
                base_temp = random.uniform(28.0, 36.0)
                base_rain = random.choices([0.0, random.uniform(1, 25)], weights=[0.7, 0.3])[0]
                session.add(Weather(
                    city_id='hanoi',
                    district_id=d.id,
                    timestamp=ts,
                    temperature=round(base_temp + random.uniform(-2, 2), 1),
                    humidity=round(random.uniform(60, 90), 1),
                    rain=round(base_rain, 1),
                    wind_speed=round(random.uniform(3, 18), 1),
                ))

                base_aqi = random.randint(80, 160)
                session.add(AQI(
                    city_id='hanoi',
                    district_id=d.id,
                    timestamp=ts,
                    pm25=round(base_aqi * 0.6, 1),
                    pm10=round(base_aqi * 0.9, 1),
                    co=round(random.uniform(0.8, 2.5), 2),
                    no2=round(random.uniform(30, 80), 1),
                    aqi_index=base_aqi + random.randint(-10, 10),
                ))

        await session.flush()

        # ── Events ─────────────────────────────────────────────────────────────
        for i, ev in enumerate(EVENTS_DATA):
            d = district_objs[i % len(district_objs)]
            session.add(Event(
                city_id='hanoi',
                district_id=d.id,
                title=ev['title'],
                category=ev['category'],
                start_time=now - timedelta(hours=random.randint(0, 6)),
                end_time=now + timedelta(hours=random.randint(2, 12)),
                impact_level=ev['impact'],
            ))

        # ── Citizen feedback ───────────────────────────────────────────────────
        for i in range(30):
            cat, sent, content = random.choice(FEEDBACK_TEMPLATES)
            d = random.choice(district_objs)
            session.add(CitizenFeedback(
                city_id='hanoi',
                district_id=d.id,
                category=cat,
                sentiment=sent,
                content=content,
            ))

        await session.commit()
        print(f'[seed] Districts: {len(district_objs)} | Weather+AQI: {len(district_objs) * 24} rows each | Events: {len(EVENTS_DATA)} | Feedback: 30')

        # ── City scores ────────────────────────────────────────────────────────
        for d in district_objs:
            await CityScoreService.calculate_and_save(session, d.id)
        await session.commit()
        print('[seed] City scores computed for all districts.')
        print('[seed] Done — ready for demo!')


if __name__ == '__main__':
    asyncio.run(run())
