from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot

from app.config import settings
from app.db.session import SessionLocal
from app.services.checker import check_prices_and_notify

def build_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)

    async def job():
        async with SessionLocal() as session:
            await check_prices_and_notify(bot, session)

    scheduler.add_job(
        job,
        trigger=IntervalTrigger(seconds=settings.CHECK_INTERVAL_SECONDS),
        id="price_check",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler
