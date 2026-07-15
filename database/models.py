"""
Ma'lumotlar bazasi sxemasi va jadvallarni yaratish (PostgreSQL).
"""
import asyncpg
import logging

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Global ulanish hovuzi (Connection Pool)
pool = None

async def init_db():
    """Ma'lumotlar bazasi va jadvallarni yaratadi."""
    global pool
    if not pool:
        logger.info("PostgreSQL ga ulanish o'rnatilmoqda...")
        pool = await asyncpg.create_pool(DATABASE_URL)

    async with pool.acquire() as conn:
        # Xodimlar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                username TEXT,
                birth_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Ta'tillar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS vacations (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)

        # Bayramlar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS holidays (
                id SERIAL PRIMARY KEY,
                holiday_name TEXT NOT NULL,
                holiday_date TEXT NOT NULL,
                is_recurring INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Adminlar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
                full_name TEXT NOT NULL,
                username TEXT,
                added_by BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sozlamalar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        logger.info("Jadvallar tekshirildi/yaratildi.")

async def close_db():
    """Ulanishni yopadi."""
    global pool
    if pool:
        await pool.close()
        pool = None
        logger.info("PostgreSQL ulanishi yopildi.")
