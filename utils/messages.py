"""
Xabar shablonlari va formatlash funksiyalari.
"""


def format_birthday_message(full_name: str, username: str | None) -> str:
    """Tug'ilgan kun tabrigi xabarini qaytaradi."""
    mention = f"@{username}" if username else full_name
    return (
        f"🎂🎉 Bugun {mention} ning tug'ilgan kuni!\n\n"
        f"Hurmatli {full_name}, tug'ilgan kuningiz muborak bo'lsin! "
        f"Sizga mustahkam sog'lik, oilaviy baxt va ishda "
        f"muvaffaqiyatlar tilaymiz! 🥳🎁\n\n"
        f"Jamoa a'zolari, qani tabriklaymiz! 👏"
    )


def format_vacation_start_message(full_name: str, username: str | None) -> str:
    """Ta'tilga chiqish xabarini qaytaradi."""
    mention = f"@{username}" if username else full_name
    return (
        f"🏖 Bugundan boshlab {mention} ({full_name}) ta'tilga chiqdilar.\n"
        f"Yaxshi dam oling! ☀️"
    )


def format_vacation_end_message(full_name: str, username: str | None) -> str:
    """Ta'tildan qaytish xabarini qaytaradi."""
    mention = f"@{username}" if username else full_name
    return (
        f"💼 {mention} ({full_name}) bugun ta'tildan qaytdilar.\n"
        f"Ishga qaytganingiz bilan! Xush kelibsiz! 🤝"
    )


def format_holiday_message(holiday_name: str) -> str:
    """Bayram tabrigi xabarini qaytaradi."""
    return (
        f"🎊 Barchangizni {holiday_name} bilan tabriklaymiz!\n"
        f"Bayramingiz muborak bo'lsin! 🎉"
    )


def format_weekend_reminder() -> str:
    """Juma kungi dam olish eslatmasini qaytaradi."""
    return "🌟 Yaxshi dam oling va kuch to'plang! Hammaga yaxshi dam olish kunlarini tilaymiz! 🏡"


def format_vacation_advance_message(
    full_name: str,
    username: str | None,
    start_date: str,
    end_date: str,
    days_left: int,
) -> str:
    """
    Ta'tilni oldindan (15 kun) e'lon qilish xabarini qaytaradi.
    """
    mention = f"@{username}" if username else full_name
    return (
        f"📢 <b>Ta'til e'loni!</b>\n\n"
        f"👤 {mention} ({full_name})\n"
        f"🏖 <b>{days_left} kundan keyin ta'tilga chiqadi</b>\n"
        f"📅 Davr: {start_date} → {end_date}\n\n"
        f"⏰ Iltimos, ish jarayonlarini oldindan rejalashtiring!"
    )


def format_employee_info(emp: dict, index: int | None = None) -> str:
    """Xodim ma'lumotlarini formatlangan matn sifatida qaytaradi."""
    prefix = f"{index}. " if index is not None else ""
    username_str = f"@{emp['username']}" if emp.get("username") else "—"
    return (
        f"{prefix}👤 {emp['full_name']}\n"
        f"   🎂 Tug'ilgan kun: {emp['birth_date']}\n"
        f"   📱 Username: {username_str}\n"
        f"   🆔 ID: {emp['id']}"
    )


def format_vacation_info(vac: dict, index: int | None = None) -> str:
    """Ta'til ma'lumotlarini formatlangan matn sifatida qaytaradi."""
    prefix = f"{index}. " if index is not None else ""
    return (
        f"{prefix}👤 {vac['full_name']}\n"
        f"   📅 {vac['start_date']} → {vac['end_date']}\n"
        f"   🆔 ID: {vac['id']}"
    )


def format_holiday_info(hol: dict, index: int | None = None) -> str:
    """Bayram ma'lumotlarini formatlangan matn sifatida qaytaradi."""
    prefix = f"{index}. " if index is not None else ""
    recurring = "🔁 Har yili" if hol.get("is_recurring") else "📌 Bir martalik"
    return (
        f"{prefix}🎉 {hol['holiday_name']}\n"
        f"   📅 Sana: {hol['holiday_date']}\n"
        f"   {recurring}\n"
        f"   🆔 ID: {hol['id']}"
    )
