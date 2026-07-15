"""
HR Reminder Bot — Asosiy ishga tushirish fayli.
Tug'ilgan kunlar, ta'tillar va bayramlarni avtomatik eslatib turuvchi bot.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.models import init_db, close_db
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.group import router as group_router
from middlewares.admin_check import AdminCheckMiddleware
from scheduler.jobs import setup_scheduler

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Bot ishga tushganda chaqiriladi."""
    # Ma'lumotlar bazasini yaratish / yangilash
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    # Bot haqida ma'lumot
    bot_info = await bot.get_me()
    logger.info(f"Bot ishga tushdi: @{bot_info.username} ({bot_info.full_name})")


async def main():
    """Asosiy funksiya — bot va schedulerni ishga tushiradi."""
    # Bot yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Dispatcher yaratish
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware qo'shish (faqat private chatdagi xabarlar uchun)
    dp.message.middleware(AdminCheckMiddleware())

    # Router'larni ulash
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(group_router)

    # Startup callback
    dp.startup.register(on_startup)

    # Scheduler sozlash va ishga tushirish
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler ishga tushdi.")

    # Polling boshlash
    try:
        logger.info("Bot polling rejimida ishga tushmoqda...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()
        await close_db()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot foydalanuvchi tomonidan to'xtatildi.")
