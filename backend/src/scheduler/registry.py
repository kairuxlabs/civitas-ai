"""Shared APScheduler instance used by both FastAPI startup (backend/src/main.py)
and DecisionSessionService, so a job scheduled from an API request lands on
the same scheduler that's actually running."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
