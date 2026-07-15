"""
/start buyrug'i va asosiy menyu.
"""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router()


def get_main_menu() -> InlineKeyboardMarkup:
    """Asosiy menyu inline klaviaturasini qaytaradi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Xodim qo'shish", callback_data="menu_add_employee"),
            InlineKeyboardButton(text="📋 Xodimlar", callback_data="menu_employees"),
        ],
        [
            InlineKeyboardButton(text="🏖 Ta'til qo'shish", callback_data="menu_add_vacation"),
            InlineKeyboardButton(text="📅 Ta'tillar", callback_data="menu_vacations"),
        ],
        [
            InlineKeyboardButton(text="🎉 Bayram qo'shish", callback_data="menu_add_holiday"),
            InlineKeyboardButton(text="📜 Bayramlar", callback_data="menu_holidays"),
        ],
        [
            InlineKeyboardButton(text="⚙️ Guruh sozlash", callback_data="menu_set_group"),
            InlineKeyboardButton(text="🛡 Adminlar", callback_data="menu_admins"),
        ],
    ])


WELCOME_TEXT = (
    "🤖 <b>HR Reminder Bot</b>ga xush kelibsiz!\n\n"
    "Bu bot quyidagi vazifalarni bajaradi:\n"
    "• 🎂 Xodimlarning tug'ilgan kunlarini tabriklab turadi\n"
    "• 🏖 Ta'tilga chiqish/qaytish haqida xabar beradi\n"
    "• 🎉 Umumiy bayramlarni eslatib turadi\n\n"
    "Quyidagi menyudan kerakli bo'limni tanlang yoki buyruqlardan foydalaning:\n\n"
    "<code>/add_employee</code> — Xodim qo'shish\n"
    "<code>/employees</code> — Xodimlar ro'yxati\n"
    "<code>/add_vacation</code> — Ta'til qo'shish\n"
    "<code>/vacations</code> — Ta'tillar ro'yxati\n"
    "<code>/add_holiday</code> — Bayram qo'shish\n"
    "<code>/holidays</code> — Bayramlar ro'yxati\n"
    "<code>/set_group</code> — Guruh ID sozlash\n"
    "<code>/admins</code> — Adminlarni boshqarish"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Bot ishga tushganda xush kelibsiz xabari va menyu."""
    await message.answer(
        WELCOME_TEXT,
        reply_markup=get_main_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu_back")
async def callback_main_menu(callback: CallbackQuery):
    """Asosiy menyuga qaytish."""
    await callback.message.edit_text(
        WELCOME_TEXT,
        reply_markup=get_main_menu(),
        parse_mode="HTML",
    )
    await callback.answer()
