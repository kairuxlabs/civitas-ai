"""
Run database migrations against Neon.tech PostgreSQL.

Usage:
    DATABASE_URL="postgresql+asyncpg://..." python -m scripts.migrate_neon

This creates all tables and seeds the 12 Hanoi districts.
Run once after provisioning a new Neon database.
"""
import asyncio
import os
import sys

# Allow running as: python -m scripts.migrate_neon from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import all models so their tables are registered on Base.metadata
from src.database.connection import Base
import src.models.district
import src.models.weather
import src.models.aqi
import src.models.city_score
import src.models.decision
import src.models.event
import src.models.feedback


async def migrate():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    print(f"Connecting to: {db_url[:40]}...")
    engine = create_async_engine(db_url, echo=True)

    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)

    # Seed districts
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        from src.models.district import District
        from sqlalchemy import select

        result = await session.execute(select(District).limit(1))
        if result.scalar_one_or_none() is not None:
            print("Districts already seeded — skipping.")
        else:
            hanoi_districts = [
                "Hoàn Kiếm", "Ba Đình", "Đống Đa", "Hai Bà Trưng", "Hoàng Mai",
                "Thanh Xuân", "Cầu Giấy", "Long Biên", "Nam Từ Liêm",
                "Bắc Từ Liêm", "Tây Hồ", "Hà Đông",
            ]
            for name in hanoi_districts:
                session.add(District(city_id="hanoi", name=name))
            await session.commit()
            print(f"Seeded {len(hanoi_districts)} districts.")

    await engine.dispose()
    print("Migration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
