import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import settings
from database import init_db
from bot.handlers import main_router
from bot.middlewares import DbMiddleware
from services.monitor import MonitorService
from utils.logger import logger


async def main():
    logger.info("🚀 Starting OLX Bot...")

    # Init DB
    await init_db()
    logger.info("✅ Database initialized")

    # Bot & dispatcher
    bot = Bot(token=settings.BOT_TOKEN)
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)

    # Middleware
    dp.message.middleware(DbMiddleware())
    dp.callback_query.middleware(DbMiddleware())

    # Routers
    dp.include_router(main_router)

    # Monitor scheduler
    monitor = MonitorService(bot)
    scheduler = AsyncIOScheduler(timezone="Europe/Kiev")
    scheduler.add_job(
        monitor.run_cycle,
        trigger="interval",
        seconds=settings.PARSE_INTERVAL_SECONDS,
        id="monitor",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"⏱ Monitor scheduler started (interval: {settings.PARSE_INTERVAL_SECONDS}s)")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("🛑 Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
