import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! .env faylini tekshiring.")

# Admin foydalanuvchilar ID'lari (vergul bilan ajratilgan)
ADMIN_IDS: list[int] = []
_admin_ids_raw = os.getenv("ADMIN_IDS", "")
if _admin_ids_raw:
    ADMIN_IDS = [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip()]

# Guruh ID (ixtiyoriy — /set_group orqali ham o'rnatiladi)
GROUP_ID = os.getenv("GROUP_ID", "")

# Vaqt zonasi va eslatma vaqti
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")
REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", "9"))
REMINDER_MINUTE = int(os.getenv("REMINDER_MINUTE", "0"))

# Ma'lumotlar bazasi fayli (PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL topilmadi! .env faylini yoki Railway sozlamalarini tekshiring.")
