"""
Kunlik eslatma vazifalari (Scheduler Jobs).
Har kuni belgilangan vaqtda bazani tekshirib, guruhga xabar yuboradi.
"""
import logging
from datetime import date, datetime, timedelta

from zoneinfo import ZoneInfo
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TIMEZONE, REMINDER_HOUR, REMINDER_MINUTE
from database import queries
from utils.messages import (
    format_birthday_message,
    format_vacation_start_message,
    format_vacation_end_message,
    format_vacation_advance_message,
    format_holiday_message,
    format_weekend_reminder,
)

# Ta'tilni necha kun oldin e'lon qilish
VACATION_ADVANCE_DAYS = 15

logger = logging.getLogger(__name__)


async def _get_group_id() -> int | None:
    """Guruh ID ni bazadan oladi."""
    group_id_str = await queries.get_setting("group_id")
    if group_id_str:
        try:
            return int(group_id_str)
        except ValueError:
            logger.error(f"Noto'g'ri group_id: {group_id_str}")
    return None


async def daily_check(bot: Bot):
    """
    Kunlik tekshirish: tug'ilgan kunlar, ta'tillar, bayramlar.
    Har kuni ertalab chaqiriladi.
    """
    group_id = await _get_group_id()
    if not group_id:
        logger.warning("Guruh ID sozlanmagan! /set_group buyrug'ini ishlating.")
        return

    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)
    today = now.date()
    today_mm_dd = today.strftime("%m-%d")
    today_yyyy_mm_dd = today.strftime("%Y-%m-%d")

    logger.info(f"Kunlik tekshirish boshlandi: {today_yyyy_mm_dd} ({today_mm_dd})")

    # 1. Tug'ilgan kunlar
    birthdays = await queries.get_birthdays_today(today_mm_dd)
    for emp in birthdays:
        try:
            msg = format_birthday_message(emp["full_name"], emp.get("username"))
            await bot.send_message(chat_id=group_id, text=msg)
            logger.info(f"Tug'ilgan kun tabrigi yuborildi: {emp['full_name']}")
        except Exception as e:
            logger.error(f"Tug'ilgan kun xabari yuborishda xato ({emp['full_name']}): {e}")

    # 2. Ta'tilga chiqishlar
    vacation_starts = await queries.get_vacation_starts_today(today_yyyy_mm_dd)
    for vac in vacation_starts:
        try:
            msg = format_vacation_start_message(vac["full_name"], vac.get("username"))
            await bot.send_message(chat_id=group_id, text=msg)
            logger.info(f"Ta'tilga chiqish xabari: {vac['full_name']}")
        except Exception as e:
            logger.error(f"Ta'til boshlanish xabari xato ({vac['full_name']}): {e}")

    # 3. Ta'tildan qaytishlar
    vacation_ends = await queries.get_vacation_ends_today(today_yyyy_mm_dd)
    for vac in vacation_ends:
        try:
            msg = format_vacation_end_message(vac["full_name"], vac.get("username"))
            await bot.send_message(chat_id=group_id, text=msg)
            logger.info(f"Ta'tildan qaytish xabari: {vac['full_name']}")
        except Exception as e:
            logger.error(f"Ta'til tugash xabari xato ({vac['full_name']}): {e}")

    # 4. Bayramlar
    holidays_today = await queries.get_holidays_today(today_yyyy_mm_dd, today_mm_dd)
    for hol in holidays_today:
        try:
            msg = format_holiday_message(hol["holiday_name"])
            await bot.send_message(chat_id=group_id, text=msg)
            logger.info(f"Bayram tabrigi: {hol['holiday_name']}")
        except Exception as e:
            logger.error(f"Bayram xabari xato ({hol['holiday_name']}): {e}")

    # 5. Ta'tilni 15 kun oldin e'lon qilish
    advance_date = today + timedelta(days=VACATION_ADVANCE_DAYS)
    advance_date_str = advance_date.strftime("%Y-%m-%d")
    upcoming_vacations = await queries.get_vacations_starting_on(advance_date_str)
    for vac in upcoming_vacations:
        try:
            msg = format_vacation_advance_message(
                full_name=vac["full_name"],
                username=vac.get("username"),
                start_date=vac["start_date"],
                end_date=vac["end_date"],
                days_left=VACATION_ADVANCE_DAYS,
            )
            await bot.send_message(chat_id=group_id, text=msg, parse_mode="HTML")
            logger.info(
                f"Ta'til e'loni yuborildi ({VACATION_ADVANCE_DAYS} kun oldin): "
                f"{vac['full_name']} — {vac['start_date']}"
            )
        except Exception as e:
            logger.error(f"Ta'til e'loni xabari xato ({vac['full_name']}): {e}")

    # 6. Juma kuni dam olish eslatmasi
    if today.weekday() == 4:  # 4 = Juma
        try:
            msg = format_weekend_reminder()
            await bot.send_message(chat_id=group_id, text=msg)
            logger.info("Juma dam olish eslatmasi yuborildi.")
        except Exception as e:
            logger.error(f"Juma eslatmasi xato: {e}")

    logger.info("Kunlik tekshirish yakunlandi.")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    APScheduler ni sozlaydi va qaytaradi.
    Har kuni REMINDER_HOUR:REMINDER_MINUTE da daily_check funksiyasi chaqiriladi.
    """
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    scheduler.add_job(
        daily_check,
        trigger="cron",
        hour=REMINDER_HOUR,
        minute=REMINDER_MINUTE,
        args=[bot],
        id="daily_reminder_check",
        name="Kunlik eslatma tekshiruvi",
        replace_existing=True,
    )

    logger.info(
        f"Scheduler sozlandi: har kuni {REMINDER_HOUR:02d}:{REMINDER_MINUTE:02d} "
        f"({TIMEZONE}) da tekshirish ishga tushadi."
    )

    return scheduler
