"""
Ma'lumotlar bazasi uchun CRUD operatsiyalar (PostgreSQL).
"""
from database import models


# ─────────────────────────────────────────────
# Xodimlar (Employees)
# ─────────────────────────────────────────────

async def add_employee(full_name: str, username: str | None, birth_date: str) -> int:
    """
    Yangi xodim qo'shadi.
    birth_date: MM-DD formatda.
    Qaytaradi: yangi yozuv id'si.
    """
    return await models.pool.fetchval(
        "INSERT INTO employees (full_name, username, birth_date) VALUES ($1, $2, $3) RETURNING id",
        full_name, username, birth_date
    )


async def get_all_employees() -> list[dict]:
    """Barcha xodimlar ro'yxatini qaytaradi."""
    rows = await models.pool.fetch(
        "SELECT id, full_name, username, birth_date FROM employees ORDER BY full_name"
    )
    return [dict(row) for row in rows]


async def get_employee(employee_id: int) -> dict | None:
    """Bitta xodimni id bo'yicha qaytaradi."""
    row = await models.pool.fetchrow(
        "SELECT id, full_name, username, birth_date FROM employees WHERE id = $1",
        employee_id
    )
    return dict(row) if row else None


async def delete_employee(employee_id: int) -> bool:
    """Xodimni o'chiradi. Qaytaradi: muvaffaqiyatli o'chirilganmi."""
    status = await models.pool.execute(
        "DELETE FROM employees WHERE id = $1", employee_id
    )
    return not status.endswith(" 0")


async def update_employee(employee_id: int, full_name: str, username: str | None, birth_date: str) -> bool:
    """Xodim ma'lumotlarini yangilaydi."""
    status = await models.pool.execute(
        "UPDATE employees SET full_name = $1, username = $2, birth_date = $3 WHERE id = $4",
        full_name, username, birth_date, employee_id
    )
    return not status.endswith(" 0")


async def get_birthdays_today(today_mm_dd: str) -> list[dict]:
    """Bugungi tug'ilgan kunlarni qaytaradi. today_mm_dd: MM-DD formatda."""
    rows = await models.pool.fetch(
        "SELECT id, full_name, username, birth_date FROM employees WHERE birth_date = $1",
        today_mm_dd
    )
    return [dict(row) for row in rows]


# ─────────────────────────────────────────────
# Ta'tillar (Vacations)
# ─────────────────────────────────────────────

async def add_vacation(employee_id: int, start_date: str, end_date: str) -> int:
    """
    Xodimga ta'til qo'shadi.
    Sanalar YYYY-MM-DD formatda.
    """
    return await models.pool.fetchval(
        "INSERT INTO vacations (employee_id, start_date, end_date) VALUES ($1, $2, $3) RETURNING id",
        employee_id, start_date, end_date
    )


async def get_all_vacations() -> list[dict]:
    """Barcha ta'tillarni xodim ismi bilan qaytaradi."""
    rows = await models.pool.fetch("""
        SELECT v.id, v.start_date, v.end_date, e.full_name, e.username
        FROM vacations v
        JOIN employees e ON v.employee_id = e.id
        ORDER BY v.start_date
    """)
    return [dict(row) for row in rows]


async def get_active_and_upcoming_vacations(today_str: str) -> list[dict]:
    """Joriy va kelgusi ta'tillarni qaytaradi. today_str: YYYY-MM-DD."""
    rows = await models.pool.fetch("""
        SELECT v.id, v.start_date, v.end_date, e.full_name, e.username
        FROM vacations v
        JOIN employees e ON v.employee_id = e.id
        WHERE v.end_date >= $1
        ORDER BY v.start_date
    """, today_str)
    return [dict(row) for row in rows]


async def delete_vacation(vacation_id: int) -> bool:
    """Ta'tilni o'chiradi."""
    status = await models.pool.execute(
        "DELETE FROM vacations WHERE id = $1", vacation_id
    )
    return not status.endswith(" 0")


async def get_vacation_starts_today(today_str: str) -> list[dict]:
    """Bugun boshlanadigan ta'tillarni qaytaradi. today_str: YYYY-MM-DD."""
    rows = await models.pool.fetch("""
        SELECT v.id, e.full_name, e.username
        FROM vacations v
        JOIN employees e ON v.employee_id = e.id
        WHERE v.start_date = $1
    """, today_str)
    return [dict(row) for row in rows]


async def get_vacations_starting_on(target_date_str: str) -> list[dict]:
    """
    Berilgan sanada boshlanadigan ta'tillarni qaytaradi (15 kun oldin ogohlantirish uchun).
    target_date_str: YYYY-MM-DD formatda.
    Qaytaradi: xodim ismi, username, boshlanish va tugash sanalari.
    """
    rows = await models.pool.fetch("""
        SELECT v.id, v.start_date, v.end_date, e.full_name, e.username
        FROM vacations v
        JOIN employees e ON v.employee_id = e.id
        WHERE v.start_date = $1
        ORDER BY e.full_name
    """, target_date_str)
    return [dict(row) for row in rows]


async def get_vacation_ends_today(today_str: str) -> list[dict]:
    """Bugun tugaydigan ta'tillarni qaytaradi. today_str: YYYY-MM-DD."""
    rows = await models.pool.fetch("""
        SELECT v.id, e.full_name, e.username
        FROM vacations v
        JOIN employees e ON v.employee_id = e.id
        WHERE v.end_date = $1
    """, today_str)
    return [dict(row) for row in rows]


# ─────────────────────────────────────────────
# Bayramlar (Holidays)
# ─────────────────────────────────────────────

async def add_holiday(holiday_name: str, holiday_date: str, is_recurring: bool) -> int:
    """
    Yangi bayram qo'shadi.
    is_recurring=True bo'lsa holiday_date MM-DD formatda,
    aks holda YYYY-MM-DD formatda.
    """
    return await models.pool.fetchval(
        "INSERT INTO holidays (holiday_name, holiday_date, is_recurring) VALUES ($1, $2, $3) RETURNING id",
        holiday_name, holiday_date, 1 if is_recurring else 0
    )


async def get_all_holidays() -> list[dict]:
    """Barcha bayramlar ro'yxatini qaytaradi."""
    rows = await models.pool.fetch(
        "SELECT id, holiday_name, holiday_date, is_recurring FROM holidays ORDER BY holiday_date"
    )
    return [dict(row) for row in rows]


async def delete_holiday(holiday_id: int) -> bool:
    """Bayramni o'chiradi."""
    status = await models.pool.execute(
        "DELETE FROM holidays WHERE id = $1", holiday_id
    )
    return not status.endswith(" 0")


async def get_holidays_today(today_yyyy_mm_dd: str, today_mm_dd: str) -> list[dict]:
    """
    Bugungi bayramlarni qaytaradi.
    Recurring bayramlar uchun MM-DD, bir martalik uchun YYYY-MM-DD tekshiriladi.
    """
    rows = await models.pool.fetch("""
        SELECT id, holiday_name, holiday_date, is_recurring
        FROM holidays
        WHERE (is_recurring = 1 AND holiday_date = $1)
           OR (is_recurring = 0 AND holiday_date = $2)
    """, today_mm_dd, today_yyyy_mm_dd)
    return [dict(row) for row in rows]


# ─────────────────────────────────────────────
# Sozlamalar (Settings)
# ─────────────────────────────────────────────

async def set_setting(key: str, value: str):
    """Sozlama qo'shadi yoki yangilaydi."""
    await models.pool.execute(
        "INSERT INTO settings (key, value) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
        key, str(value)
    )


async def get_setting(key: str) -> str | None:
    """Sozlama qiymatini qaytaradi."""
    row = await models.pool.fetchrow(
        "SELECT value FROM settings WHERE key = $1", key
    )
    return row["value"] if row else None


# ─────────────────────────────────────────────
# Adminlar (Admins)
# ─────────────────────────────────────────────

async def add_admin(user_id: int, full_name: str, username: str | None, added_by: int | None = None) -> bool:
    """Yangi admin qo'shadi."""
    await models.pool.execute(
        "INSERT INTO admins (user_id, full_name, username, added_by) VALUES ($1, $2, $3, $4) ON CONFLICT (user_id) DO UPDATE SET full_name = EXCLUDED.full_name, username = EXCLUDED.username, added_by = EXCLUDED.added_by",
        user_id, full_name, username, added_by
    )
    return True

async def get_all_admins() -> list[dict]:
    """Barcha adminlarni qaytaradi."""
    rows = await models.pool.fetch("SELECT user_id, full_name, username, added_by, created_at FROM admins")
    return [dict(row) for row in rows]

async def get_admin(user_id: int) -> dict | None:
    """Adminni qaytaradi."""
    row = await models.pool.fetchrow("SELECT user_id, full_name, username, added_by, created_at FROM admins WHERE user_id = $1", user_id)
    return dict(row) if row else None

async def delete_admin(user_id: int) -> bool:
    """Adminni o'chiradi."""
    status = await models.pool.execute("DELETE FROM admins WHERE user_id = $1", user_id)
    return not status.endswith(" 0")
