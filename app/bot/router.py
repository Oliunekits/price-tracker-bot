from aiogram import Router
from app.bot.handlers import start, add_tracker, list_trackers, rate

root_router = Router()
root_router.include_router(start.router)
root_router.include_router(rate.router)
root_router.include_router(add_tracker.router)
root_router.include_router(list_trackers.router)
