from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import text

import src.models.aqi  # noqa: F401
import src.models.district  # noqa: F401
import src.models.weather  # noqa: F401
from src.database.connection import Base, engine
from src.main import _ensure_hot_path_indexes


@pytest.mark.asyncio
async def test_ensure_hot_path_indexes_does_not_raise_on_sqlite():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # CREATE INDEX IF NOT EXISTS must be a safe no-crash no-op path on the
    # SQLite test dialect, exactly like it is against the real Render
    # Postgres database (which create_all never retroactively touches).
    await _ensure_hot_path_indexes()

    async with engine.connect() as conn:
        weather_result = await conn.execute(text("PRAGMA index_list('weather')"))
        weather_indexes = {row[1] for row in weather_result}
        aqi_result = await conn.execute(text("PRAGMA index_list('aqi')"))
        aqi_indexes = {row[1] for row in aqi_result}

    assert "idx_weather_district_ts" in weather_indexes
    assert "idx_aqi_district_ts" in aqi_indexes


@pytest.mark.asyncio
async def test_ensure_hot_path_indexes_swallows_errors(monkeypatch):
    import src.main as main_module

    broken_conn = MagicMock()
    broken_conn.execute = AsyncMock(side_effect=RuntimeError("db unavailable"))

    class _BrokenBeginCtx:
        async def __aenter__(self):
            return broken_conn

        async def __aexit__(self, *exc):
            return None

    class _FakeEngine:
        def begin(self):
            return _BrokenBeginCtx()

    # AsyncEngine.begin is a read-only attribute, so swap out the whole
    # module-level `engine` reference `_ensure_hot_path_indexes` looks up
    # instead of patching the real engine instance.
    monkeypatch.setattr(main_module, "engine", _FakeEngine())

    # Must not raise — a failure here should never block app startup.
    await _ensure_hot_path_indexes()
